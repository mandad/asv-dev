""""
Plans a new path based on a recorded path and swath

Damian Manda
damian.manda@noaa.gov
12 Feb 2015
"""

import numpy as np
import beamtrace

def unit_vector(vector):
    """
    Expects vector as a tuple (or probably array/list would work)
    """
    #vec_array = np.array(vector, dtype=np.float)
    mag = np.linalg.norm(vector)
    return vector / mag

class PathPlan(object):
    def __init__(self, swath_record, side, margin=0.2):
        self.swath_record = swath_record
        if side == 'port' or side == 'stbd':
            self.side = side
        else:
            raise Exception('Invalid side')
        self.margin = margin

    def generate_next_path(self):
        print('Generating Next Path')
        edge_pts = self.swath_record.get_swath_outer_pts(self.side)
        
        print (len(edge_pts))
        
        next_path_pts = []
        # so this isn't very pythonic, but I need before and after...
        for i in range(len(edge_pts)):
            # There should always be either a forward or back heading
            # I made there be both for the average (or you could avoid averaging - probably faster)
            back_vec = None
            if i > 0:
                back_vec = np.array([ edge_pts[i][0] - edge_pts[i-1][0], \
                 edge_pts[i][1] - edge_pts[i-1][1] ], dtype=np.float)
            if i < len(edge_pts)-2:
                forward_vec = np.array([ edge_pts[i+1][0] - edge_pts[i][0], \
                 edge_pts[i+1][1] - edge_pts[i][1] ], dtype=np.float)
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
        return next_path_pts
