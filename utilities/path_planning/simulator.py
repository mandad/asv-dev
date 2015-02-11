import followpath
import beamtrace
import gridgen

class Simulator(object):
    def __init__(start_x, start_y, resolution):
        self.vehicle = followpath.Vehicle(start_x, start_y, 0)
        self.vehicle.set_sim_resolution(resolution)
        self.path = followpath.Path()
        self.follower = followpath.FollowPath(self.vehicle, self.path)
        self.swath_record = followpath.RecordSwath(5)

        self.veh_locs = []
        self.port_outer = []
        self.stbd_outer = []

        self.generate_grid()
        self.generate_path()

    def generate_grid(self):
        pass

    def generate_path(self):
        pass

    def iterate(self):
        pass

    def record_swath_point(self):
        pass