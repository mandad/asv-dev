import numpy as np
import beamtrace

def vector_from_heading(heading, length):
    raise NotImplementedError()

def next_pos(x0, y0, heading, length):
    hdg_vec = vector_from_heading(heading, length)
    return (x0 + hdg_vec[0], y0 + hdg_vec[1])

def hdg_to_point(cur_x, cur_y, wpt_x, wpt_y):
    raise NotImplementedError()

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
        self.waypoints = []
        self.cur_wpt = 0;

    def add_waypoint(self, *args):
        if len(args) == 1:
            self.waypoints.append(args[0])
        elif len(args) == 2:
            wpt = Waypoint(args[0], args[1])
            self.waypoints.append(wpt)

    def get_cur_wpt(self):
        if len(self.waypoints) > 0:
            return self.waypoints[self.cur_wpt]
        else:
            return None

    def mark_cur_visited(self):
        if len(self.waypoints) > 0:
            # Does this work?
            self.waypoints[cur_wpt].visit()

    def get_next_wpt(self):
        if len(self.waypoints) > self.cur_wpt:
            return self.waypoints[self.cur_wpt + 1]
        else:
            return None

    def increment_wpt(self):
        if len(self.waypoints) > self.cur_wpt:
            self.cur_wpt =  self.cur_wpt + 1
            return True
        else:
            return False

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

    def record(self, swath, loc_x, loc_y, heading):
        rec = np.array([loc_x, loc_y, heading, swath])
        self.full_record.append(rec)
        self.interval_record.append(rec)
        np.append(interval_swath, swath)

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
        idx = interval_swath.argmin()
        # Add the first point if this is the first interval
        if len(min_record) == 0 and idx != 0:
            min_record.append(interval_record[0])
        self.min_record.append(interval_record[idx])
        self.interval_record = []
        self.interval_swath = np.array([])

    def reset_line(self):
        self.interval_record = []
        self.interval_swath = np.array([])
        self.full_record = []   # this is only for visualization
        self.min_record = []
        self.acc_dist = 0

    def get_swath_outer_pts(self):
        outer_rec = []
        for record in self.min_record:
            hdg_x, hdg_y = vector_from_heading(record[2])
            beam_dx, beam_dy = beamtrace.hdg_to_beam(hdg_x, hdg_y, 'stbd')


class FollowPath(object):
    def __init__(self, vehicle, path):
        self.vehicle = vehicle
        self.path = path
        #self.swath_record = RecordSwath(5) # this should be in the overall planning class

        #Initialize track
        # veh_x, veh_y = self.vehicle.get_location()
        first_wpt = self.path.get_cur_wpt()
        if first_wpt is not None:
            self.vehicle.hdg = hdg_to_point(self.vehicle.x, self.vehicle.y, \
                first_wpt.x, first_wpt.y)

    def increment(self):
        cur_wpt = path.get_cur_wpt()
        # Check if reached next waypoint
        if (abs(self.vehicle.x) - cur_wpt.x) <= self.vehicle.resolution \
            and (abs(self.vehicle.y) - cur_wpt.y) <= self.vehicle.resolution:
            # Put it exactly at the waypoint
            self.vehicle.set_location(cur_wpt.x, cur_wpt.y)
            path.mark_cur_visited()
            if self.path.increment_wpt():
                # The next is now the "current"
                next_wpt = self.path.get_cur_wpt()
                # Note that this does not transistion headings between lines
                self.vehicle.hdg = hdg_to_point(cur_wpt.x, cur_wpt.y, \
                    next_wpt.x, next_wpt.y)
            else:
                # Reached the last waypoint
                return False

        self.vehicle.advance_position()
        return True

    def get_vehicle_loc(self):
        return self.vehicle.get_location()
