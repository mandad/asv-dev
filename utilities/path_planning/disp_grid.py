import simulator
import sys

def show_grid(gtype, view_3D=False):
    sim = simulator.Simulator(0, 0, .5, gtype)
    sim.bathy_grid.disp_grid(view_3D)
    wait = raw_input()

if __name__ == '__main__':
    show_grid(sys.argv[1])