"""
Encapsulates overall simulation functions

Damian Manda
damian.manda@noaa.gov
12 Feb 2015
"""

import followpath
import beamtrace
import gridgen
import matplotlib.pyplot as plt

class Simulator(object):
    def __init__(self, start_x, start_y, resolution, swath_interval=10):
        self.vehicle = followpath.Vehicle(start_x, start_y, 0)
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
        start_loc = self.follower.get_vehicle_loc()
        self.path.add_waypoint(start_loc[0], start_loc[1])
        if waypoints is not None:
            for waypoint in waypoints:
                self.path.add_waypoint(waypoint[0], waypoint[1])

    def add_waypoints(self, waypoints):
        for waypoint in waypoints:
            self.path.add_waypoint(waypoint[0], waypoint[1])

    # iterates over one path
    def iterate(self):
        if self.follower.increment():
            this_loc = self.follower.get_vehicle_loc()
            hdg_deg = self.follower.get_vehicle_hdg()
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

    def run_simulation(self):
        try:
            while self.iterate():
                pass
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
        plt.legend()

        plt.axis('equal')
        plt.show()
