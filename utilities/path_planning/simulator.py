"""
Encapsulates overall simulation functions

Damian Manda
damian.manda@noaa.gov
11 Feb 2015
"""

import followpath
import beamtrace
import gridgen
import pathplan
import matplotlib.pyplot as plt
import numpy as np
import copy

new_path_side = ['port', 'stbd']

class Simulator(object):
    def __init__(self, start_x, start_y, resolution, grid_type='hump', swath_interval=10):
        self.vehicle = followpath.Vehicle(start_x, start_y, 90)
        self.vehicle.set_sim_resolution(resolution)
        self.path = followpath.Path()
        self.follower = followpath.FollowPath(self.vehicle, self.path)
        self.swath_record = dict()
        self.prev_swath = dict()
        self.swath_record['port'] = followpath.RecordSwath(swath_interval)
        self.swath_record['stbd'] = followpath.RecordSwath(swath_interval)

        self.veh_locs = [(start_x, start_y)]
        self.port_outer = []
        self.stbd_outer = []
        self.swath_angle = 65

        self.op_poly = None
        self.generate_grid(gtype=grid_type)
        self.generate_path()

    def generate_grid(self, size_x=1000, size_y=1000, gtype='hump'):
        self.bathy_grid = gridgen.BathyGrid(size_x, size_y, 1)
        if gtype == 'hump':
            self.bathy_grid.generate_hump(20, 15, 'y')
        elif gtype == 'flat':
            self.bathy_grid.generate_flat(25)
        elif gtype =='slope':
            self.bathy_grid.generate_slope(10, 40)

    def generate_path(self, waypoints=None):
        """
        waypoints is a list of (x, y) tuples
        """
        self.path.clear()
        start_loc = self.follower.get_vehicle_loc()
        self.path.add_waypoint(start_loc[0], start_loc[1])
        if waypoints is not None:
            self.add_waypoints(waypoints)

    def add_waypoints(self, waypoints):
        for waypoint in waypoints:
            self.path.add_waypoint(waypoint[0], waypoint[1])

    # iterates over one path
    def iterate(self):
        if self.follower.increment():
            this_loc = self.follower.get_vehicle_loc()
            hdg_deg = self.follower.get_vehicle_hdg()
            # Don't record going to the first waypoint (0 = cur_loc, 1 = first pt)
            # and cur_wpt is the one the vessel is going toward
            if self.path.cur_wpt > 1:
                self.record_swath_point(this_loc, hdg_deg)
            self.veh_locs.append(this_loc)
            return True
        else:
            # Record last point
            if len(self.swath_record['stbd'].interval_record) > 0:
                self.swath_record['stbd'].min_interval()
            if len(self.swath_record['port'].interval_record) > 0:
                self.swath_record['port'].min_interval()
            return False

    def run_simulation(self, num_lines=2):
        try:
            for i in range(num_lines):
                print('\n======== Following Line {0} ========'.format(i+1))
                while self.iterate():
                    pass

                # Shouldn't run this the final time, it erases the swath record
                if i < num_lines - 1:
                    # Plan a new path on the starboard side
                    path_planner = pathplan.PathPlan(self.swath_record[new_path_side[i % 2]], \
                        new_path_side[i % 2], 0.2)
                    next_path = path_planner.generate_next_path(self.op_poly)
                    print('New Path Length: {0}'.format(len(next_path)))

                    # xy_pts = zip(*next_path)
                    # plt.plot(xy_pts[0], xy_pts[1], 'bo-')
                    # plt.axis('equal')
                    # plt.show()

                    # Run the second path
                    if len(next_path) < 2:
                        return True
                    self.generate_path(next_path)
                    
                    # Check if have to turn from first position, if so we are done
                    # TODO: Think through this logic a bit more systematically
                    veh_pos = self.path.get_cur_wpt()
                    line_start = self.path.get_next_wpt()
                    line_second_pt = self.path.get_wpt(2)
                    vec_to_start = np.array([line_start.x - veh_pos.x, line_start.y - veh_pos.y])
                    vec_first_leg = np.array([line_second_pt.x - line_start.x, \
                        line_second_pt.y - line_start.y])
                    if pathplan.PathPlan.vector_angle(vec_to_start, vec_first_leg) > 90:
                        return True

                    self.prev_swath = copy.deepcopy(self.swath_record)
                    self.swath_record['stbd'].reset_line()
                    self.swath_record['port'].reset_line()

        except KeyboardInterrupt:
            return False
        return True

    def set_operation_polygon(self, vertices):
        """
        vertices is a list of (x,y) tuples
        Assumes the polygon has been checked before passing to the function
        """
        self.op_poly = vertices

    def record_swath_point(self, this_loc, hdg_deg):
        """
        Convert heading to vector, get perpendicular, ray trace it, then store this depth
        In normal operation, we would just get the heading and loc from vehicle and swath
        from the sonar
        """
        hdg_x, hdg_y = followpath.vector_from_heading(hdg_deg, 1)

        # Record port side swath
        beam_x, beam_y = beamtrace.hdg_to_beam(hdg_x, hdg_y, 'port')
        ray_trace = beamtrace.ray_depth(self.bathy_grid, self.swath_angle, \
            this_loc[0], this_loc[1], beam_x, beam_y, 1)
        swath_width = beamtrace.width_from_depth(self.swath_angle, ray_trace[2])
        self.swath_record['port'].record(swath_width, this_loc[0], this_loc[1], hdg_deg)

        # Record stbd side swath
        beam_x, beam_y = beamtrace.hdg_to_beam(hdg_x, hdg_y, 'stbd')
        ray_trace = beamtrace.ray_depth(self.bathy_grid, self.swath_angle, \
            this_loc[0], this_loc[1], beam_x, beam_y, 1)
        swath_width = beamtrace.width_from_depth(self.swath_angle, ray_trace[2])
        self.swath_record['stbd'].record(swath_width, this_loc[0], this_loc[1], hdg_deg)

    def plot_sim(self):
        # Plot the path that was followed
        xy_locs = zip(*self.veh_locs)
        plt.plot(xy_locs[0], xy_locs[1], label='Vessel Path')

        # Swath Edge
        swath_edge = self.swath_record['port'].get_swath_outer_pts('port')
        swath_xy_port = zip(*swath_edge)
        swath_edge = self.swath_record['stbd'].get_swath_outer_pts('stbd')
        swath_xy_stbd = zip(*swath_edge)
        plt.plot(swath_xy_port[0], swath_xy_port[1], 'ro-', label='Swath Edge Port')
        plt.plot(swath_xy_stbd[0], swath_xy_stbd[1], 'go-', label='Swath Edge Stbd')

        # First Swath
        if len(self.prev_swath) > 0:
            swath_edge = self.prev_swath['port'].get_swath_outer_pts('port')
            prev_swath_xy_port = zip(*swath_edge)
            swath_edge = self.prev_swath['stbd'].get_swath_outer_pts('stbd')
            prev_swath_xy_stbd = zip(*swath_edge)
            plt.plot(prev_swath_xy_port[0], prev_swath_xy_port[1], 'r--', label='Prev Edge Port')
            plt.plot(prev_swath_xy_stbd[0], prev_swath_xy_stbd[1], 'g--', label='Prev Edge Stbd')

        plt.legend()

        plt.axis('equal')
        plt.show()
