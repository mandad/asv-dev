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
import copy

new_path_side = ['port', 'stbd']

class Simulator(object):
    def __init__(self, start_x, start_y, resolution, swath_interval=10):
        self.vehicle = followpath.Vehicle(start_x, start_y, 90)
        self.vehicle.set_sim_resolution(resolution)
        self.path = followpath.Path()
        self.follower = followpath.FollowPath(self.vehicle, self.path)
        self.swath_record = dict()
        self.swath_record['port'] = followpath.RecordSwath(swath_interval)
        self.swath_record['stbd'] = followpath.RecordSwath(swath_interval)

        self.veh_locs = [(start_x, start_y)]
        self.port_outer = []
        self.stbd_outer = []
        self.swath_angle = 65

        self.generate_grid()
        self.generate_path()

    def generate_grid(self):
        self.bathy_grid = gridgen.BathyGrid(1000, 1000, 1)
        self.bathy_grid.generate_hump(20, 15, 'y')

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
                #print('I\'m fucking storing this shit {0}'.format(self.path.cur_wpt))
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
                while self.iterate():
                    pass

                # Shouldn't run this the final time, it erases the swath record
                if i < num_lines - 1:
                    # Plan a new path on the starboard side
                    path_planner = pathplan.PathPlan(self.swath_record[new_path_side[i % 2]], \
                        new_path_side[i % 2], 0.2)
                    next_path = path_planner.generate_next_path()
                    print('New Path Length: {0}'.format(len(next_path)))

                    # xy_pts = zip(*next_path)
                    # plt.plot(xy_pts[0], xy_pts[1], 'bo-')
                    # plt.axis('equal')
                    # plt.show()

                    # Run the second path
                    self.generate_path(next_path)
                    self.prev_swath = copy.deepcopy(self.swath_record)
                    self.swath_record['stbd'].reset_line()
                    self.swath_record['port'].reset_line()
            

        except KeyboardInterrupt:
            return False
        return True


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
        swath_edge = self.prev_swath['port'].get_swath_outer_pts('port')
        prev_swath_xy_port = zip(*swath_edge)
        swath_edge = self.prev_swath['stbd'].get_swath_outer_pts('stbd')
        prev_swath_xy_stbd = zip(*swath_edge)
        plt.plot(prev_swath_xy_port[0], prev_swath_xy_port[1], 'r--', label='Prev Edge Port')
        plt.plot(prev_swath_xy_stbd[0], prev_swath_xy_stbd[1], 'g--', label='Prev Edge Stbd')

        plt.legend()

        plt.axis('equal')
        plt.show()
