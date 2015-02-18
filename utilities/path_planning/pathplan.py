""""
Plans a new path based on a recorded path and swath

Damian Manda
damian.manda@noaa.gov
12 Feb 2015
"""

import numpy as np
import beamtrace
import pdb
# from lsi import lsi

np.set_printoptions(suppress=True)

def unit_vector(vector):
    """
    Expects vector as a tuple (or probably array/list would work)
    """
    #vec_array = np.array(vector, dtype=np.float)
    mag = np.linalg.norm(vector)
    return vector / mag

class PathPlan(object):
    """Handles functions for planning a subsequent survey line given information
    about an existing one

    Arguments:
    swath_record - the record of swath minimums and locations from the last line
    side - whether to plan on the port or stbd side of the last path
    margin - the amount of overlap desired between swaths
    """
    def __init__(self, swath_record, side, margin=0.2):
        self.swath_record = swath_record
        if side == 'port' or side == 'stbd':
            self.side = side
        else:
            raise Exception('Invalid side')
        self.margin = margin

    def generate_next_path(self, op_poly=None):
        print('Generating Next Path')
        edge_pts = self.swath_record.get_swath_outer_pts(self.side)
        # pdb.set_trace()
        
        print ('Basis Points: {0}'.format(len(edge_pts)))
        
        next_path_pts = []
        # so this isn't very pythonic, but I need before and after...
        for i in range(len(edge_pts)):
            # There should always be either a forward or back heading
            # I made there be both for the average (or you could avoid averaging - probably faster)
            back_vec = None
            if i > 0:
                back_vec = np.array([edge_pts[i][0] - edge_pts[i-1][0], \
                 edge_pts[i][1] - edge_pts[i-1][1]], dtype=np.float)
            if i < len(edge_pts)-2:
                forward_vec = np.array([edge_pts[i+1][0] - edge_pts[i][0], \
                 edge_pts[i+1][1] - edge_pts[i][1]], dtype=np.float)
            else:
                forward_vec = back_vec
            if back_vec is None:
                back_vec = forward_vec

            # ** All of this could be done in a vector operation, just duplicate first
            # and last points in the record arrays

            # average heading
            back_vec = unit_vector(back_vec)
            forward_vec = unit_vector(forward_vec)
            avg_vec = (back_vec + forward_vec) / 2

            # Get the offset vector
            offset_dx, offset_dy = beamtrace.hdg_to_beam(avg_vec[0], avg_vec[1], self.side)
            swath_width = self.swath_record.get_swath_width(i)
            offset_vector = np.array([offset_dx * swath_width, \
                offset_dy * swath_width])
            offset_vector = offset_vector * (1 - self.margin)

            # Get offset location and save
            swath_loc = np.array(edge_pts[i])
            next_pt = tuple(swath_loc + offset_vector)
            next_path_pts.append(next_pt)

        # Next line is in opposite direction
        next_path_pts.reverse()

        # pdb.set_trace()
        # Eliminate points not in op region
        # Eventually needs to see if paths intersect the boundaries as well
        print('Eliminating points outside op region.')
        if op_poly is not None:
            next_path_pts = [pt for pt in next_path_pts if self.point_in_poly(pt[0], pt[1], op_poly)]
        
        # Check for overlapping paths
        # brute force this for now as a solution to adjacent paths
        # pdb.set_trace()
        print('Eliminating path bends on itself.')
        # These arrays will never be longer than next_path_points, could be faster to pre-allocate
        # and then delete unused ones at the end
        intersect_pts = []
        non_intersect_idx = np.array([], dtype=np.int64)
        i = 0
        while i < (len(next_path_pts) - 3):
            seg_pts = []
            non_intersect_idx = np.append(non_intersect_idx, i)
            this_seg_a = next_path_pts[i]
            this_seg_b = next_path_pts[i+1]
            for j in range(i + 2, len(next_path_pts)-1):
                check_seg_a = next_path_pts[j]
                check_seg_b = next_path_pts[j+1]
                if self.intersect(this_seg_a, this_seg_b, check_seg_a, check_seg_b):
                    seg_pts.append(j+1)
            if len(seg_pts) > 0:
                # Store the last one it intersects with, want to remove indexes btwn these
                intersect_pts.append((i+1, seg_pts[-1]))
                i = seg_pts[-1] + 1
            else:
                i = i + 1

        # Add the last segment as long as it was not overlapping
        if i < len(next_path_pts):
            # Normal end, have three points left
            non_intersect_idx = np.append(non_intersect_idx, [i, i + 1, i + 2])
        else:
            non_intersect_idx = np.append(non_intersect_idx, len(next_path_pts) - 1)


        next_path_pts = np.array(next_path_pts)
        next_path_pts = next_path_pts[non_intersect_idx]

        #   Check for drastic angles between segments

        # return [tuple(x) for x in pts_np]
        # pdb.set_trace()
        return next_path_pts

    @staticmethod
    def  point_in_poly(x, y, poly):
        """ Determines if a given point is inside a polygon
        x, y -- x and y coordinates of point
        a list of tuples [(x, y), (x, y), ...]
        """
        num = len(poly)
        i = 0
        j = num - 1
        c = False
        for i in range(num):
            if  ((poly[i][1] > y) != (poly[j][1] > y)) and \
                    (x < (poly[j][0] - poly[i][0]) * (y - poly[i][1]) / \
                        (poly[j][1] - poly[i][1]) + poly[i][0]):
                c = not c
            j = i
        return c

    @staticmethod
    def ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    @staticmethod
    def intersect(A, B, C, D):
        # Does not check for colinearity
        return PathPlan.ccw(A, C, D) != PathPlan.ccw(B, C, D) and \
            PathPlan.ccw(A, B, C) != PathPlan.ccw(A, B, D)

