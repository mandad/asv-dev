"""
Defines classes to simulate a vessel or vehicle following a path of (x, y)
waypoints and record a simulated sonar swath at these points using the bathymetic
grid defined by gridgen.py

Damian Manda
9 Feb 2015
"""

import numpy as np
import beamtrace
from shapely.geometry import Polygon, MultiPoint, Point, MultiPolygon
import shapely.ops
import pdb

def vector_from_heading(heading, length):
    hdg_rad = np.radians(heading)
    # Rounding makes ~0 => 0 (from numerical sin/cos)
    return (round(length * np.sin(hdg_rad), 15), round(length * np.cos(hdg_rad), 15))

def next_pos(x0, y0, heading, length):
    hdg_vec = vector_from_heading(heading, length)
    return (x0 + hdg_vec[0], y0 + hdg_vec[1])

def hdg_to_point(cur_x, cur_y, wpt_x, wpt_y, heading_basis=0):
    vec_x = wpt_x - cur_x
    vec_y = wpt_y - cur_y

    if round(vec_x, 15) == 0 and round(vec_y, 15) == 0:
        # Keep heading same if next waypoint is the same
        return heading_basis
    else:
        hdg = np.degrees(np.math.atan2(vec_x, vec_y))
        if hdg < 0:
            hdg = 360 + hdg
        return hdg

class Vehicle(object):
    def __init__(self, start_x, start_y, start_hdg):
        self.x = start_x
        self.y = start_y
        self.hdg = start_hdg
        self.resolution = 0.1

    def set_sim_resolution(self, res):
        self.resolution = res

    def get_location(self):
        return (self.x, self.y)

    def set_location(self, set_x, set_y):
        self.x = set_x
        self.y = set_y

    def advance_position(self):
        self.x, self.y = next_pos(self.x, self.y, self.hdg, self.resolution)

class Path(object):
    def __init__(self):
        self.clear()
        self.cur_wpt = 0

    def add_waypoint(self, *args):
        if len(args) == 1:
            self.waypoints.append(args[0])
        elif len(args) == 2:
            wpt = Waypoint(args[0], args[1])
            self.waypoints.append(wpt)

    def get_cur_wpt(self):
        #print("Getting wpt: {0}".format(self.cur_wpt))
        if len(self.waypoints) > 0:
            return self.waypoints[self.cur_wpt]
        else:
            return None

    def mark_cur_visited(self):
        if len(self.waypoints) > 0:
            # Does this work?
            self.waypoints[self.cur_wpt].visit()

    def get_next_wpt(self):
        if len(self.waypoints) - 1 > self.cur_wpt:
            return self.waypoints[self.cur_wpt + 1]
        else:
            return None

    def get_wpt(self, index):
        if index < len(self.waypoints):
            return self.waypoints[index]
        else:
            return None

    def increment_wpt(self):
        if len(self.waypoints) - 1 > self.cur_wpt:
            self.cur_wpt = self.cur_wpt + 1
            return True
        else:
            return False

    def clear(self):
        self.waypoints = []
        self.cur_wpt = 0

class Waypoint(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.visited = False

    def visit(self):
        self.visited = True

class RecordSwath(object):
    def __init__(self, interval):
        self.interval_record = []
        self.interval_swath = np.array([])
        self.full_record = []   # this is only for visualization
        # Or we could only record the whole thing and process at the end of the line
        self.min_record = []
        self.interval = interval
        self.acc_dist = 0
        #needed if no full record
        self.last_x = None
        self.last_y = None

        self.coverage = Polygon()

    def record(self, swath, loc_x, loc_y, heading):
        rec = np.array([loc_x, loc_y, heading, swath])
        self.full_record.append(rec)
        self.interval_record.append(rec)
        self.interval_swath = np.append(self.interval_swath, swath)

        if self.last_x is not None and self.last_y is not None:
            # Calculate distance from last recorded position
            self.acc_dist = self.acc_dist + np.linalg.norm((loc_x - self.last_x, \
                loc_y - self.last_y))
            if self.acc_dist > self.interval:
                self.acc_dist = 0
                self.min_interval()
        self.last_x = loc_x
        self.last_y = loc_y

    def min_interval(self):
        idx = self.interval_swath.argmin()
        # Add the first point if this is the first interval
        if len(self.min_record) == 0 and idx != 0:
            self.min_record.append(self.interval_record[0])
        self.min_record.append(self.interval_record[idx])
        self.interval_record = []
        self.interval_swath = np.array([])

    def reset_line(self):
        self.interval_record = []
        self.interval_swath = np.array([])
        self.full_record = []   # this is only for visualization
        self.min_record = []
        self.acc_dist = 0
        self.coverage = Polygon()

    # Right now we just record one side, picked to be stbd here - should be both
    # Doesn't cache the points because this would in theory only be called once
    def get_swath_outer_pts(self, side='stbd'):
        """Get the outer points along a swath"""
        outer_rec = []
        for record in self.min_record:
            outer_pt = self.get_outer_point(record[0], record[1], record[2], \
                record[3], side)
            outer_rec.append(outer_pt)
        return outer_rec

    def get_swath_coverage(self, side='stbd'):
        """Get the full recorded swath coverage
        Intersects polygons along the line in order to avoid problems with having to generate
        a concave hull to the outer points, and incorrect polygon from intersecting segments
        as each set of points will always form a quadrilateral or triangle
        """
        step_polygons = []
        first_record = self.full_record[0]
        # rec = np.array([loc_x, loc_y, heading, swath])
        last_outer_pt = self.get_outer_point(first_record[0], \
            first_record[1], first_record[2], first_record[3], side)
        last_pos = (first_record[0], first_record[1])
        for record in self.full_record[1:]:
            this_outer_pt = self.get_outer_point(record[0], record[1], \
                record[2], record[3], side)
            this_pos = (record[0], record[1])
            swath_add = MultiPoint([last_outer_pt, last_pos, this_pos, this_outer_pt])
            step_polygons.append(swath_add.convex_hull)
            
            # Store for next iteration
            last_outer_pt = this_outer_pt
            last_pos = this_pos

        return shapely.ops.unary_union(step_polygons)

    @staticmethod
    def get_outer_point(loc_x, loc_y, heading, swath, side):
        hdg_x, hdg_y = vector_from_heading(heading, 1)
        beam_dx, beam_dy = beamtrace.hdg_to_beam(hdg_x, hdg_y, side)
        outer_pt = (loc_x + beam_dx * swath, loc_y + beam_dy * swath)
        return outer_pt

    def get_swath_width(self, index):
        return self.min_record[index][3]

    def get_swath_location(self, index):
        return (self.min_record[index][0], self.min_record[index][1])

    # For if I decide to integrate port/stbd recording
    @staticmethod
    def append_ps(ps_array, port, stbd):
        if ps_array is None:
            ps_array = np.array([[port, stbd]])
        else:
            ps_array = np.concatenate(ps_array[[port, stbd]])

        return ps_array

    @staticmethod
    def get_port(ps_array):
        return ps_array[:, 0]

    @staticmethod
    def get_stbd(ps_array):
        return ps_array[:, 1]


class FollowPath(object):
    def __init__(self, vehicle, path):
        self.vehicle = vehicle
        self.path = path

        #Initialize track
        first_wpt = self.path.get_cur_wpt()
        if first_wpt is not None:
            self.vehicle.hdg = hdg_to_point(self.vehicle.x, self.vehicle.y, \
                first_wpt.x, first_wpt.y, self.vehicle.hdg)

    def increment(self):
        cur_wpt = self.path.get_cur_wpt()
        # Check if reached next waypoint
        if (abs(self.vehicle.x - cur_wpt.x)) <= self.vehicle.resolution \
            and (abs(self.vehicle.y - cur_wpt.y)) <= self.vehicle.resolution:
            # Put it exactly at the waypoint
            print('At Waypoint {0}'.format(self.path.cur_wpt))
            self.vehicle.set_location(cur_wpt.x, cur_wpt.y)
            self.path.mark_cur_visited()
            if self.path.increment_wpt():
                # The next is now the "current"
                next_wpt = self.path.get_cur_wpt()
                # Note that this does not transistion headings between lines
                self.vehicle.hdg = hdg_to_point(cur_wpt.x, cur_wpt.y, \
                    next_wpt.x, next_wpt.y, self.vehicle.hdg)
                print('Now on hdg {0:.2f}'.format(self.vehicle.hdg))
            else:
                # Reached the last waypoint
                return False

        self.vehicle.advance_position()
        return True

    def get_vehicle_loc(self):
        return self.vehicle.get_location()

    def get_vehicle_hdg(self):
        return self.vehicle.hdg
