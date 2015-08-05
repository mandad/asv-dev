""""
Plans a new path based on a recorded path and swath

Damian Manda
damian.manda@noaa.gov
18 Feb 2015
"""

import numpy as np
import beamtrace
import pdb
import matplotlib.pyplot as plt
import matplotlib.path as mplPath
import pprint
import shapely.geometry as sg
from descartes.patch import PolygonPatch
BLUE = '#6699cc'
GRAY = '#999999'

RESTRICT_ASV_TO_REGION = True

# from lsi import lsi
np.set_printoptions(suppress=True)
MAX_BEND_ANGLE = 60 # degrees
DEBUG_PLOTS = False

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
    def __init__(self, swath_record, side, margin=0.2, edge_pts = None, swath_widths = None):
        if swath_record is None:
            self.edge_pts_input = edge_pts
            self.swath_record = None
        else:
            self.swath_record = swath_record
            self.edge_pts_input = None

        self.swath_widths = swath_widths

        if side == 'port' or side == 'stbd':
            self.side = side
        else:
            raise Exception('Invalid side')
        self.margin = margin

    def generate_next_path(self, op_poly=None):
        """Generates a new path based on the previous swath, and restricts operation
        to the passed region.
        """
        print('\n======== Generating Next Path ========')
        if self.edge_pts_input is None:
            edge_pts = self.swath_record.get_swath_outer_pts(self.side)
        else:
            edge_pts = self.edge_pts_input
        next_path_pts = []

        print ('Basis Points: {0}'.format(len(edge_pts)))
        # Only clip the basis swath to region, not the vehicle path
        if not RESTRICT_ASV_TO_REGION:
            pre_len = len(edge_pts)
            # Eliminate points not in op region
            # Eventually needs to see if paths intersect the boundaries as well - current does
            # not result in full coverage
            print('Eliminating basis points outside op region.')
            if op_poly is not None:
                edge_pts = [pt for pt in edge_pts if self.point_in_poly(pt[0], pt[1], op_poly)]
            print('Removed {0} points.\n'.format(pre_len - len(edge_pts)))
            pre_len = len(edge_pts)

            # Done with op region (in nieve case)
            if pre_len == 0:
                return next_path_pts

        if len(edge_pts) < 2:
            return next_path_pts

        # ---------- Generate Path -----------
        # so this isn't very pythonic, but I need before and after...
        for i in range(len(edge_pts)):
            # There should always be either a forward or back heading
            # I made there be both for the average (or you could avoid averaging - probably faster)
            back_vec = None
            if i > 0:
                back_vec = np.array([edge_pts[i][0] - edge_pts[i-1][0], \
                 edge_pts[i][1] - edge_pts[i-1][1]], dtype=np.float)
            if i < len(edge_pts)-1:
                forward_vec = np.array([edge_pts[i+1][0] - edge_pts[i][0], \
                 edge_pts[i+1][1] - edge_pts[i][1]], dtype=np.float)
            else:
                forward_vec = back_vec
            if back_vec is None:
                back_vec = forward_vec

            # TODO: All of this could be done in a vector operation, just duplicate first
            # and last points in the record arrays

            # average heading
            back_vec = unit_vector(back_vec)
            forward_vec = unit_vector(forward_vec)
            avg_vec = (back_vec + forward_vec) / 2

            # Get the offset vector
            offset_dx, offset_dy = beamtrace.hdg_to_beam(avg_vec[0], avg_vec[1], self.side)
            if self.swath_widths is None:
                swath_width = self.swath_record.get_swath_width(i)
            else:
                swath_width = self.swath_widths[i]
            offset_vector = np.array([offset_dx * swath_width, \
                offset_dy * swath_width])
            offset_vector = offset_vector * (1 - self.margin)

            # Get offset location and save
            swath_loc = np.array(edge_pts[i])
            next_pt = tuple(swath_loc + offset_vector)
            next_path_pts.append(next_pt)

        # Next line is in opposite direction
        next_path_pts.reverse()

        # Note that the meaning of pre_len switches here
        pre_len = len(next_path_pts)

        orig_pts = next_path_pts[:]

        if DEBUG_PLOTS:
            xy_path0 = zip(*next_path_pts)
            plt.plot(xy_path0[0], xy_path0[1], 'go-', label='Before Intersect', markersize=8)

        # ---------- Intersections -----------
        print('Eliminating path intersects itself.')
        next_path_pts = np.array(next_path_pts)
        next_path_pts = self.remove_all(self.remove_intersects, next_path_pts)

        print('Removed {0} points.\n'.format(pre_len - len(next_path_pts)))
        pre_len = len(next_path_pts)

        if DEBUG_PLOTS:
            xy_path = zip(*next_path_pts)
            plt.plot(xy_path[0], xy_path[1], 'bs-', label='Before Bends', markersize=6)
            plt.axis('equal')

        # ---------- Bends -----------
        print('Eliminating dramatic bends.')
        next_path_pts = self.remove_all(self.remove_bends, next_path_pts)

        print('Removed {0} points.\n'.format(pre_len - len(next_path_pts)))
        pre_len = len(next_path_pts)

        if DEBUG_PLOTS and pre_len > 0:
            xy_path2 = zip(*next_path_pts)
            plt.plot(xy_path2[0], xy_path2[1], 'r^-', label='After Bends', markersize=6)

        # ---------- Restrict to Region -----------
        if RESTRICT_ASV_TO_REGION:
            print('Eliminating points outside op region.')
            if op_poly is not None:
                next_path_pts = [pt for pt in next_path_pts if self.point_in_poly(pt[0], pt[1], op_poly)]
            print('Removed {0} points.\n'.format(pre_len - len(next_path_pts)))
            pre_len = len(next_path_pts)

            # Done with op region (in nieve case)
            if pre_len <= 1:
                return next_path_pts

        if DEBUG_PLOTS and pre_len > 0:
            xy_path3 = zip(*next_path_pts)
            plt.plot(xy_path3[0], xy_path3[1], 'k+-', label='After Op Region', markersize=6)
            plt.legend(loc='best')
            plt.show()
            pdb.set_trace()

        # ---------- Extend -----------
        print('Extending ends of path to edge of region.')
        next_path_pts_extend = np.array(next_path_pts, copy=True)
        # Extend end points to edge of op region
        if op_poly is not None and pre_len > 1:
            for i, segments in enumerate([(1,0), (len(next_path_pts)-2, len(next_path_pts) - 1)]): 
                extend_vec = next_path_pts[segments[1]] - next_path_pts[segments[0]]
                starting_pt = next_path_pts[segments[1]]
                intersection = self.find_nearest_intersect(extend_vec, starting_pt, op_poly)
                # Make sure we aren't extending too far
                if self.swath_record is None:
                    extend_max = 100
                else:
                    extend_max = 15 * self.swath_record.interval
                if intersection[0] < extend_max:
                    # First or last point
                    if i == 0:
                        next_path_pts_extend = np.insert(next_path_pts_extend, 0, intersection[1], 0)
                    else:
                        next_path_pts_extend = np.append(next_path_pts_extend, [intersection[1]], 0)

        next_path_pts = next_path_pts_extend
        print('Added {0} points.\n'.format(len(next_path_pts) - pre_len))

        return next_path_pts

    @staticmethod 
    def remove_all(process, path_pts):
        """Repeats a process until it makes no more changes to the path
        Currently does not make a copy of the passed input, may want to reconsider this
        """
        pre_len = len(path_pts)
        path_pts = process(path_pts)
        # keep repeating until no more changes
        while len(path_pts) < pre_len:
            pre_len = len(path_pts)
            path_pts = process(path_pts)

        return path_pts

    @staticmethod
    def remove_intersects(path_pts):
        """Check for overlapping paths
        # brute force this for now as a solution to adjacent paths

        # These arrays will never be longer than path_pts, could be faster to pre-allocate
        # and then delete unused ones at the end since a new array is created each
        # time np.append runs
        """
        intersect_pts = []
        non_intersect_idx = np.array([], dtype=np.int64)
        i = 0
        while i < (len(path_pts) - 3):
            seg_pts = []
            non_intersect_idx = np.append(non_intersect_idx, i)
            this_seg_a = path_pts[i]
            this_seg_b = path_pts[i+1]
            # Check all following segments
            for j in range(i + 2, len(path_pts)-1):
                check_seg_a = path_pts[j]
                check_seg_b = path_pts[j+1]
                if PathPlan.intersect(this_seg_a, this_seg_b, check_seg_a, check_seg_b):
                    seg_pts.append(j+1)
            if len(seg_pts) > 0:
                # Store the last one it intersects with, want to remove indexes btwn these
                intersect_pts.append((i+1, seg_pts[-1]))
                i = seg_pts[-1]
            else:
                i = i + 1

        # Add the last segment as long as it was not overlapping
        if i < len(path_pts):
            # Normal end, have three points left
            non_intersect_idx = np.append(non_intersect_idx, np.arange(i, len(path_pts)))
        else:
            non_intersect_idx = np.append(non_intersect_idx, len(path_pts) - 1)

        return path_pts[non_intersect_idx]

    @staticmethod 
    def remove_bends_gradient(path_pts):
        # sec_grad = np.gradient(np.gradient(path_pts)[0])[0]
        # sec_grad_sum = np.sum(sec_grad,1)
        # non_bend_idx = np.abs(sec_grad_sum - np.average(sec_grad_sum)) < (np.std(sec_grad_sum) * 1.5)
        # pprint.pprint(sec_grad_sum)
        grad = np.gradient(path_pts)[0]
        slope = grad[:,1]/grad[:,0]
        pprint.pprint(slope)
        del_slp = np.gradient(slope)
        pprint.pprint(del_slp)
        non_bend_idx = del_slp < 2
        return path_pts[non_bend_idx]

    @staticmethod
    def remove_bends(path_pts):
        """Check for drastic angles between segments
        # Note that this goes to the last point being checked
        # There has got to be a more efficient way to do this
        """
        # TODO: think through the recursive logic a bit more 
        # if len(path_pts) < 4:
        #     return path_pts

        # Maybe should process in both directions, remove pts common to both
        non_bend_idx = [0]
        this_seg = np.array([0, 1])
        next_seg = np.array([1, 2])
        
        while next_seg[1] < len(path_pts) - 1:
            this_vec = path_pts[this_seg[1]] - path_pts[this_seg[0]]
            next_vec = path_pts[next_seg[1]] - path_pts[next_seg[0]]
            # pprint.pprint(non_bend_idx)
            # Angle between this and following
            if PathPlan.vector_angle(this_vec, next_vec) > MAX_BEND_ANGLE:
                # If too large, have to find the next point that makes it small enough
                # -- Method 1: Points from end of current --
                test_seg = next_seg + [0, 1]
                while test_seg[1] < len(path_pts) - 1:
                    test_vec = path_pts[test_seg[1]] - path_pts[test_seg[0]]
                    angle1 = PathPlan.vector_angle(this_vec, test_vec)
                    if angle1 < MAX_BEND_ANGLE:
                        break
                    test_seg = test_seg + [0, 1]
                pts_elim1 = test_seg[1] - test_seg[0]

                # -- Method 2: Points from beginning of current --
                # check if it would be better to remove the end of "this_vec"
                if len(non_bend_idx) > 1:
                    test2_vec1 = PathPlan.vec_from_seg(path_pts, \
                        np.array([non_bend_idx[-2], this_seg[0]]))
                    test2_seg2 = np.array([this_seg[0], next_seg[1]])
                    while test2_seg2[1] < len(path_pts) - 1:
                        test2_vec2 = PathPlan.vec_from_seg(path_pts, test2_seg2)
                        angle2 = PathPlan.vector_angle(test2_vec1, test2_vec2)
                        if angle2 < MAX_BEND_ANGLE:
                            break
                        test2_seg2 = test2_seg2 + [0, 1]
                    pts_elim2 = test2_seg2[1] - test2_seg2[0]

                    # Check if one method angle is better
                    # may need to refine this threshold or only use angle
                    # really needs to be total points removed in region that would
                    # have been affected by the other method, but this requires additional
                    # loops to know
                    if pts_elim1 > pts_elim2 and pts_elim1 < (pts_elim2 * 2) and angle1 < angle2:
                        print(('Bend Fudging - pts_elim1: {0}, pts_elim2: {1}\n' + \
                            '\tangle1: {2:.2f}, angle2: {3:.2f}').format(pts_elim1, \
                            pts_elim2, angle1, angle2))
                        pts_elim2 = pts_elim1 + 1
                    elif pts_elim2 >= pts_elim1 and pts_elim2 < (pts_elim1 * 2) and angle2 < angle1:
                        print(('Bend Fudging - pts_elim1: {0}, pts_elim2: {1}\n' + \
                            '\tangle1: {2:.2f}, angle2: {3:.2f}').format(pts_elim1, \
                            pts_elim2, angle1, angle2))
                        pts_elim1 = pts_elim2 + 1
                else:
                    # force it to not choose this method
                    pts_elim2 = pts_elim1 + 1

                # Make the new vector to check next
                if pts_elim1 <= pts_elim2:
                    this_seg = test_seg
                    next_seg = np.array([test_seg[1], test_seg[1]+1])
                else:
                    this_seg = test2_seg2
                    next_seg = np.array([test2_seg2[1], test2_seg2[1]+1])
            else:
                this_seg = next_seg
                next_seg = next_seg + 1
            # don't re-add an existing index
            if non_bend_idx[-1] != this_seg[0]:
                non_bend_idx.append(this_seg[0])

        if this_seg[1] == len(path_pts) - 1:
            # Looped to the end, this indicates a large skip, otherwise we don't
            # get to the last index for this_seg, so remove the test point which
            # could be causing the problem
            all_ind = range(len(path_pts))
            #this might also work with this_seg[0]+1
            all_ind.remove(this_seg[0]) 
            # might want to put this recursion path at the end
            return PathPlan.remove_bends(path_pts[all_ind])
        else:
            # Extend to the end of the path
            non_bend_idx.extend(range(this_seg[1], len(path_pts)))

        # Remove the end if it causes a bend
        while len(non_bend_idx) > 2:
            end_angle = PathPlan.vector_angle(PathPlan.vec_from_seg(path_pts, \
                [non_bend_idx[-3], non_bend_idx[-2]]), PathPlan.vec_from_seg( \
                path_pts, [non_bend_idx[-2], non_bend_idx[-1]]))
            if end_angle > MAX_BEND_ANGLE:
                non_bend_idx.pop()
            else:
                break

        # pprint.pprint(non_bend_idx)
        non_bend_idx = np.unique(non_bend_idx)

        #if only have first seg + last point
        if non_bend_idx.size <= 3 and len(path_pts) > 5:
            # Try again eliminating the first segment
            return PathPlan.remove_bends(path_pts[1:])
        else:
            return path_pts[non_bend_idx]

    @staticmethod
    def vec_from_seg(points, segment):
        try:
            vector = points[segment[1]] - points[segment[0]]
        # Index out of bounds
        except Exception:
            vector = None
        return vector

    # TODO: All these methods need to be moved to a geometry utilities library
    @staticmethod
    def find_nearest_intersect(ray_vector, start_pt, poly):
        """ Finds the closest intersection of a ray with a polygon

        Arguments:
        ray_vector: array(dx,dy)
        start_pt: array(x,y)
        poly: array([(x1,y1), (x2,y2), ...])
        """
        num_vtx = len(poly)
        # Could pre-fill these to len(poly)
        intersect_dist = np.array([])
        intersect_pts = []
        for vtx_idx1 in range(num_vtx):
            if vtx_idx1 < (num_vtx - 1):
                vtx_idx2 = vtx_idx1 + 1
            else:
                vtx_idx2 = 0
            poly_seg = np.array([poly[vtx_idx1], poly[vtx_idx2]])
            intersection = PathPlan.intersect_ray_segment(ray_vector, start_pt, poly_seg)
            if intersection is not None:
                intersect_dist = np.append(intersect_dist, \
                    np.linalg.norm(intersection - start_pt))
                intersect_pts.append(tuple(intersection))
                # pdb.set_trace()

        # Will this work if equadistant from two?
        near_pt = intersect_pts[intersect_dist.argmin()]
        return (intersect_dist.min(), np.array(near_pt))


    @staticmethod
    def intersect_ray_segment(ray_vector, start_pt, segment):
        """http://stackoverflow.com/questions/563198/how-do-you-detect-where-two-line-segments-intersect/565282#565282
        """
        seg_start = segment[0]
        seg_vector = segment[1] - segment[0]
        rxs = np.cross(ray_vector, seg_vector)
        if rxs == 0:
            return None
        else:
            t = np.cross(seg_start - start_pt, seg_vector) / rxs
            u = np.cross(seg_start - start_pt, ray_vector) / rxs
            if t >= 0 and u >= 0 and u <= 1:
                return start_pt + t * ray_vector
            else:
                return None


    @staticmethod
    def point_in_poly(x, y, poly):
        """ Determines if a given point is inside a polygon
        x, y -- x and y coordinates of point
        a list of tuples [(x, y), (x, y), ...]
        """
        # pdb.set_trace()

        # sh_poly = sg.Polygon(poly)
        # plt.figure()
        # plt.gca().add_patch(PolygonPatch(sh_poly, facecolor=BLUE, edgecolor=GRAY, alpha=0.7, zorder=2))
        # plt.show()
        # pdb.set_trace()
        # return sh_poly.contains(sg.Point(x,y))

        # bb_path = mplPath.Path(np.array(poly), closed=True)
        # return bb_path.contains_point((x, y))

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

    @staticmethod
    def vector_angle(vector1, vector2):
        """ Returns the angle in degrees between vectors 'vector1' and 'vector2'
        Tan(ang) = |(axb)|/(a.b)
        cos(ang) = (a.b)/(||a||*||b||)
        """
        # cosang = np.dot(vector1, vector2)
        # sinang = np.linalg.norm(np.cross(vector1, vector2))
        dotp = np.dot(vector1, vector2)
        mags = np.linalg.norm(vector1) * np.linalg.norm(vector2)
        # avoid division by zero
        if mags == 0:
            return 0
        return np.arccos(dotp/mags) * 180/np.pi

