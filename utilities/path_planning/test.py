import beamtrace
import gridgen
import followpath
import numpy as np
import matplotlib.pyplot as plt


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

def test_swath_record():
    # Vehicle and path following
    vehicle = followpath.Vehicle(0, 0, 90)
    vehicle.set_sim_resolution(1)
    path = followpath.Path()
    path.add_waypoint(0, 0)
    #path.add_waypoint(50, 10)
    path.add_waypoint(100, 0)
    
    #path.add_waypoint(20, 30)
    #path.add_waypoint(15, 60)
    #path.add_waypoint(0, 100)
    #path.add_waypoint(100, 100)
    follower = followpath.FollowPath(vehicle, path)

    # Sonar simulation
    swath_record_port = followpath.RecordSwath(5)
    swath_record_stbd = followpath.RecordSwath(5)
    bg = gridgen.BathyGrid(100, 100, 1)
    # bg.generate_slope(10, 25)
    bg.generate_hump(20, 15)

    locs = [follower.get_vehicle_loc()]
    # Misses the first swath, but this is before the vehicle turns to follow the path anyway
    while follower.increment():
        try:
            this_loc = follower.get_vehicle_loc()

            # Convert heading to vector, get perpendicular, ray trace it, then store this depth
            # In normal operation, we would just get the heading and loc from vehicle and swath
            # from the sonar
            hdg_deg = follower.get_vehicle_hdg() 
            hdg_x, hdg_y = followpath.vector_from_heading(hdg_deg, 1)
            #print('heading: {0}, hdg_x: {1}, hdx_y: {2}'.format(hdg_deg, hdg_x, hdg_y))

            # Record port side swath
            beam_x, beam_y = beamtrace.hdg_to_beam(hdg_x, hdg_y, 'port')
            # print('port beam_x: {0}, beam_y: {1}'.format(beam_x, beam_y))
            ray_trace = beamtrace.ray_depth(bg, swath_angle, this_loc[0], this_loc[1], \
                beam_x, beam_y, 1)
            swath_width = beamtrace.width_from_depth(swath_angle, ray_trace[2])
            # print('port swath: {0}'.format(swath_width))
            swath_record_port.record(swath_width, this_loc[0], this_loc[1], hdg_deg)

            # Record stbd side swath
            beam_x, beam_y = beamtrace.hdg_to_beam(hdg_x, hdg_y, 'stbd')
            # print('stbd beam_x: {0}, beam_y: {1}'.format(beam_x, beam_y))
            ray_trace = beamtrace.ray_depth(bg, swath_angle, this_loc[0], this_loc[1], \
                beam_x, beam_y, 1)
            swath_width = beamtrace.width_from_depth(swath_angle, ray_trace[2])
            # print('stbd swath: {0}'.format(swath_width))
            swath_record_stbd.record(swath_width, this_loc[0], this_loc[1], hdg_deg)

            locs.append(this_loc)
        except KeyboardInterrupt:
            break

    # Force last record
    if len(swath_record_stbd.interval_record) > 0:
        swath_record_stbd.min_interval()
    if len(swath_record_port.interval_record) > 0:
        swath_record_port.min_interval()

    # Plot the path that was followed
    xy = zip(*locs)
    plt.plot(xy[0], xy[1], label='Vessel Path')

    # Swath Edge
    swath_edge = swath_record_port.get_swath_outer_pts('port')
    swath_xy_port = zip(*swath_edge)
    swath_edge = swath_record_stbd.get_swath_outer_pts('stbd')
    swath_xy_stbd = zip(*swath_edge)
    plt.plot(swath_xy_port[0], swath_xy_port[1], 'ro-', label='Swath Edge Port')
    plt.plot(swath_xy_stbd[0], swath_xy_stbd[1], 'go-', label='Swath Edge Stbd')
    plt.legend()

    plt.axis('equal')
    plt.show()
    return swath_record_stbd

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
    run_tests()
