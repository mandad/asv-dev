import beamtrace
import gridgen
import followpath
import simulator
import numpy as np
import matplotlib.pyplot as plt
import sys


swath_angle = 65

def test_beam_trace(x0, y0, hdg_x, hdg_y):
    bg = gridgen.BathyGrid(100, 100, 1)
    bg.generate_slope(10, 25)

    # Translate heading to beam direction (stbd side)
    beam_dx, beam_dy = beamtrace.hdg_to_beam(hdg_x, hdg_y, 'stbd')

    nadir_depth = beamtrace.ray_depth(bg, 0, x0, y0, beam_dx, beam_dy, 0.1)
    edge_depth = beamtrace.ray_depth(bg, swath_angle, x0, y0, beam_dx, beam_dy, 1)
    swath = beamtrace.width_from_depth(swath_angle, edge_depth[2])

    return (nadir_depth, edge_depth, swath)

def test_follow_path():
    vehicle = followpath.Vehicle(0, 0, 90)
    vehicle.set_sim_resolution(.5)

    path = followpath.Path()
    path.add_waypoint(0, 0)
    #path.add_waypoint(50, 10)
    path.add_waypoint(100, 0)

    follower = followpath.FollowPath(vehicle, path)

    locs = [follower.get_vehicle_loc()]
    while follower.increment():
        locs.append(follower.get_vehicle_loc())

    # Plot the path that was followed
    xy = zip(*locs)
    plt.plot(xy[0], xy[1])
    plt.axis('equal')
    plt.show()
    return locs

def test_swath_sim(gtype):
    sim = simulator.Simulator(0, 0, .5, gtype)
    sim.add_waypoints([(0,0), (1000, 0)])
    # One big square to start
    sim.set_operation_polygon([(0,0), (0,1000), (1000, 1000), (1000, 0)])
    if sim.run_simulation(3):
        sim.plot_sim()

def run_tests():
    # at shallow end, changing depth
    beam_info = test_beam_trace(0, 100, 1, 0)
    assert beam_info[0] == (0, 100, 10), 'Wrong Nadir Depth'
    assert [round(x, 2) for x in beam_info[1]] == [0.0, 68.28, 14.7], 'Wrong Outer Beam Depth'
    assert round(beam_info[2], 2) == 31.52, 'Wrong Swath Width'

    # at deep end, along the changing depth axis
    beam_info = test_beam_trace(0, 0, -1, 0)
    assert beam_info[0] == (0, 0, 25), 'Wrong Nadir Depth'
    assert [round(x, 2) for x in beam_info[1]] == [0.0, 40.78, 18.94], 'Wrong Outer Beam Depth'
    assert round(beam_info[2], 2) == 40.62, 'Wrong Swath Width'


if __name__ == '__main__':
    """
    heading_angle = 0;
    #beam_info = test_beam_trace(0, 0, 0, 1)    # along the constant depth axis
    #beam_info = test_beam_trace(0, 0, 1, 0)     # along the changing depth axis
    beam_info = test_beam_trace(0, 100, -1, 0)  # at shallow end, changing depth
    print('Depths:\nNadir: {0:.2f}\nEdge: {1:.2f}\n\nWidth: {2:.2f}'.format(beam_info[0][2], beam_info[1][2], \
        beam_info[2]))
    print('Intersection of outer beam: x={0:.2f}, y={1:.2f}'.format(beam_info[1][0], beam_info[1][1]))
    """
    if len(sys.argv) > 1:
        test_swath_sim(sys.argv[1])
    else:
        test_swath_sim()
