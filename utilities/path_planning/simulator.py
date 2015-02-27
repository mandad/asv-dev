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
from descartes.patch import PolygonPatch
from shapely.geometry import Polygon, MultiPoint, Point, MultiPolygon
import shapely.geometry
from shapely.prepared import prep
import copy
import pdb

NEXT_PATH_SIDE = ['port', 'stbd']
SWATH_OVERLAP = 0.2
RAY_TRACE_RES = 1.0
PRINT_DEBUG = False
BLUE = '#6699cc'
GRAY = '#999999'

class Simulator(object):
    def __init__(self, start_x, start_y, resolution, grid_type='hump', \
        swath_interval=10, bathy_file=None):
        self.vehicle = followpath.Vehicle(start_x, start_y, 90)
        self.vehicle.set_sim_resolution(resolution)
        self.path = followpath.Path()
        self.follower = followpath.FollowPath(self.vehicle, self.path)
        self.swath_record = dict()
        self.prev_swath = dict()
        self.swath_record['port'] = followpath.RecordSwath(swath_interval)
        self.swath_record['stbd'] = followpath.RecordSwath(swath_interval)
        self.coverage = Polygon()
        self.holiday_polys = []

        self.veh_locs = [(start_x, start_y)]
        self.port_outer = []
        self.stbd_outer = []
        self.swath_angle = 65
        self.last_port_depth = 0
        self.last_stbd_depth = 0

        self.op_poly = None
        if grid_type == 'file':
            if bathy_file is not None:
                self.grid_from_file(bathy_file)
            else:
                raise Exception('No bathymetry filename specified.')
        else:
            self.generate_grid(gtype=grid_type)
        self.generate_path()

    def generate_grid(self, size_x=1000, size_y=1000, gtype='hump'):
        """Generate a bathymetry grid with the designated pattern

        Arguments:
        size_x - x dimension width of the grid
        size_y - y dimension width of the grid
        gtype - the type of grid to create
        """
        self.bathy_grid = gridgen.BathyGrid(size_x, size_y, 1)
        if gtype == 'hump':
            self.bathy_grid.generate_hump(20, 15, 'y')
        elif gtype == 'dip':
            self.bathy_grid.generate_dip(25, 20, 'x')
        elif gtype == 'flat':
            self.bathy_grid.generate_flat(25)
        elif gtype == 'slope':
            self.bathy_grid.generate_slope(10, 40)
        elif gtype == 'x':
            self.bathy_grid.generate_x(25, 20)
        elif gtype == 'x_hole':
            self.bathy_grid.generate_x_hole(30, 20)
        elif gtype == 'x_bump':
            self.bathy_grid.generate_x_bump(30, 20)
        elif gtype == 'hole':
            self.bathy_grid.generate_hole(30, 20)
        elif gtype == 'bump':
            self.bathy_grid.generate_bump(30, 20)

    def grid_from_file(self, filename):
        self.bathy_grid = gridgen.BathyGrid.from_bathymetry(filename, False)

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
        """Add all waypoints to the stored path

        Arguments:
        waypoints - The list of waypoints in the form (x,y).  Can be anything
            accessible with array indexing
        """
        for waypoint in waypoints:
            self.path.add_waypoint(waypoint[0], waypoint[1])

    def set_operation_polygon(self, vertices):
        """
        vertices is a list of (x,y) tuples
        Assumes the polygon has been checked before passing to the function
        """
        self.op_poly = vertices

    def iterate(self):
        """Iterate over one path length, adding swaths to the record as we go"""
        if self.follower.increment():
            this_loc = self.follower.get_vehicle_loc()
            if PRINT_DEBUG:
                print('Current Location: {0}'.format(this_loc))
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
            this_loc[0], this_loc[1], beam_x, beam_y, RAY_TRACE_RES, self.last_port_depth)
        self.last_port_depth = ray_trace[2]
        swath_width = beamtrace.width_from_depth(self.swath_angle, ray_trace[2])
        if PRINT_DEBUG:
            print('Port Depth: {0:.2f}\tSwath: {1:.2f}'.format(ray_trace[2], swath_width))
        self.swath_record['port'].record(swath_width, this_loc[0], this_loc[1], hdg_deg)

        # Record stbd side swath
        beam_x, beam_y = beamtrace.hdg_to_beam(hdg_x, hdg_y, 'stbd')
        ray_trace = beamtrace.ray_depth(self.bathy_grid, self.swath_angle, \
            this_loc[0], this_loc[1], beam_x, beam_y, RAY_TRACE_RES, self.last_stbd_depth)
        self.last_stbd_depth = ray_trace[2]
        swath_width = beamtrace.width_from_depth(self.swath_angle, ray_trace[2])
        if PRINT_DEBUG:
            print('Stbd Depth: {0:.2f}\tSwath: {1:.2f}'.format(ray_trace[2], swath_width))
        self.swath_record['stbd'].record(swath_width, this_loc[0], this_loc[1], hdg_deg)

    def run_simulation(self, num_lines=2):
        try:
            for i in range(num_lines):
                print('\n======== Following Line {0} ========'.format(i+1))
                while self.iterate():
                    pass

                # Add swath to full coverage polygon geometry
                print('-- Adding Swath Coverage --')
                # pdb.set_trace()
                new_coverage = self.swath_record['stbd'].get_swath_coverage('stbd')
                new_coverage = new_coverage.union(self.swath_record['port'].get_swath_coverage('port'))
                self.coverage = self.coverage.union(new_coverage)

                # Shouldn't run this the final time, it erases the swath record
                if i < num_lines - 1:
                    # Plan a new path on the starboard side
                    path_planner = pathplan.PathPlan(self.swath_record[NEXT_PATH_SIDE[i % 2]], \
                        NEXT_PATH_SIDE[i % 2], SWATH_OVERLAP)
                    next_path = path_planner.generate_next_path(self.op_poly)
                    new_len = len(next_path)
                    print('New Path Length: {0}'.format(new_len))

                    # Remove pts on the path that are in the coverage
                    # TODO: Move this to pathplan.py
                    print('Eliminating Points In Existing Coverage')
                    prepared_coverage = prep(self.coverage)
                    next_path = [pt for pt in next_path if not prepared_coverage.contains(Point(tuple(pt)))]
                    print('Removed {0} points'.format(new_len - len(next_path)))
                    # pdb.set_trace()

                    # Run the second path
                    if len(next_path) < 2:
                        break
                    self.generate_path(next_path)

                    self.prev_swath = copy.deepcopy(self.swath_record)
                    self.swath_record['stbd'].reset_line()
                    self.swath_record['port'].reset_line()
            
            # Holiday determination
            try:
                int_polys = [shapely.geometry.polygon.asPolygon(int_ring) \
                    for int_ring in self.coverage.interiors]
                if len(int_polys) > 0: 
                    int_areas = np.array([poly.area for poly in int_polys])
                    holidays = np.argwhere(int_areas > 3)
                    # pdb.set_trace()
                    self.holiday_polys = [int_polys[int(i)] for i in holidays]
            except AttributeError:
                self.holidays_polys = []

        except KeyboardInterrupt:
            return False
        return True

    def plot_sim(self, show_swath=True):
        # Plot the operation region
        if self.op_poly is not None:
            plot_poly = list(self.op_poly)
            plot_poly.append(plot_poly[0])
            poly_x, poly_y = zip(*plot_poly)
            plt.plot(poly_x, poly_y, 'k', linewidth=3.0, label='Operation Region')

        # Plot the path that was followed
        xy_locs = zip(*self.veh_locs)
        # change the 'b' to 'w' for figures
        plt.plot(xy_locs[0], xy_locs[1], 'w', linewidth=2.0, label='Vessel Path')

        if show_swath:
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
                plt.plot(prev_swath_xy_port[0], prev_swath_xy_port[1], 'rs--', \
                    label='Prev Edge Port')
                plt.plot(prev_swath_xy_stbd[0], prev_swath_xy_stbd[1], 'gs--', \
                    label='Prev Edge Stbd')

        # pdb.set_trace()
        # Plot the coverage recorded
        if type(self.coverage) is Polygon:
            plt.gca().add_patch(PolygonPatch(self.coverage, facecolor=BLUE, edgecolor=GRAY, alpha=0.5, zorder=2))
        else:
            ax = plt.gca()
            for polygon in self.coverage:
                if type(polygon) is Polygon:
                    patch = PolygonPatch(polygon, facecolor=BLUE, edgecolor=GRAY, alpha=0.5, zorder=2)
                    ax.add_patch(patch)

        # Plot Holiday centroids
        holiday_cent_x = []
        holiday_cent_y = []
        for holiday_poly in self.holiday_polys:
             this_x, this_y = holiday_poly.centroid.xy
             holiday_cent_x.append(this_x)
             holiday_cent_y.append(this_y)
        if len(holiday_cent_x) > 0:
            plt.plot(holiday_cent_x, holiday_cent_y, 'm*', label='Holidays')

        # plt.legend()
        plt.axis('equal')
        self.bathy_grid.disp_grid(False, True)

        # For saving output
        # plt.ylim([-100, 1100])
        plt.savefig('path_output.png', dpi=600, transparent=True)

        plt.show()

    @staticmethod
    def plot_coords(ax, ob):
        x, y = ob.xy
        ax.plot(x, y, 'o', color='#999999', zorder=1)
