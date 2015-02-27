import beamtrace
import followpath
import simulator
import gridgen
import pathplan
import numpy as np
import matplotlib.pyplot as plt
import sys
import pdb

swath_angle = 65

def test_path_bend(scenario=0):
    path_points = [(90, 120), (105, 140), (112, 160), (160, 180), (130, 110), \
        (112, 150), (107, 155), (115, 185), (120, 190), (125, 215), (170, 275)]
    xy_pts = zip(*path_points)
    path_points = np.array(path_points)

    #process
    path_points = pathplan.PathPlan.remove_all(pathplan.PathPlan.remove_bends, path_points)
    xy_pts2 = zip(*path_points)

    plt.plot(xy_pts[0], xy_pts[1], 'bo-')
    plt.plot(xy_pts2[0], xy_pts2[1], 'rs-', markersize=2)
    plt.axis('equal')
    plt.show()

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

def test_swath_sim(gtype='slope', num_lines=5):
    sim = simulator.Simulator(0, 0, .5, gtype)
    # ===== Starting Line =======
    # Regular, start along x axis
    sim.add_waypoints([(0, 0), (1000, 0)])

    # 90 degree rotated
    # sim = simulator.Simulator(1000, 0, .5, gtype)
    # sim.add_waypoints([(1000, 0), (1000, 1000)])

    # 45 degrees
    # sim.add_waypoints([(0, 20), (20, 0)])

    # ===== Operation Region =====
    # One big square to start
    sim.set_operation_polygon([(0,0), (0,1000), (1000, 1000), (1000, 0)])

    if sim.run_simulation(num_lines):
        # use plot_sim(False) to not show swaths
        sim.plot_sim(True)
        pdb.set_trace()

def test_swath_sim_import(terrain='flat', num_lines=2):
    if terrain == 'flat':
        filename = 'terrain/Flat_Region.tif'
        sim = simulator.Simulator(359535.0, 4761987.0, 0.5, 'file', 10, filename)
        sim.add_waypoints([(359535, 4761987), (359758, 4762349)])
        sim.set_operation_polygon([(359535, 4761987), (359758, 4762349), \
            (359568, 4762486), (359491, 4762666), (359188, 4762833), \
            (358943, 4762316)])
    elif terrain == 'complex':
        filename = 'terrain/Complex_Region.tif'
        #359650.0, 4762540.0
        op_poly = [(359813.0, 4762520.0), (360270, 4763310), \
            (359617, 4763633), (359147, 4762830)]
        sim = simulator.Simulator(op_poly[0][0], op_poly[0][1], 0.5, 'file', 10, filename)
        sim.add_waypoints(op_poly[0:2])
        sim.set_operation_polygon(op_poly)

    if sim.run_simulation(num_lines):
        # use plot_sim(False) to not show swaths
        sim.plot_sim(True)
        pdb.set_trace()

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
    if len(sys.argv) == 2:
        test_swath_sim(sys.argv[1])
    elif len(sys.argv) == 3:
        if sys.argv[1] == '--terrain':
            test_swath_sim_import(sys.argv[2])
        else:
            test_swath_sim(sys.argv[1], int(sys.argv[2]))
    elif len(sys.argv) == 4:
        if sys.argv[1] == '--terrain':
            test_swath_sim_import(sys.argv[2], int(sys.argv[3]))
    else:
        test_swath_sim()
