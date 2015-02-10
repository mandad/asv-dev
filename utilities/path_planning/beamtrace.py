import numpy as np
#def unit_vector(vector)

# beam_dx = +-hdg_dy
# beam_dy = -+hdg_dx
def hdg_to_beam(hdg_x, hdg_y, dir='stbd'):
    if dir == 'stbd':
        beam_dx = -hdg_y
        beam_dy = hdg_x
    elif dir == 'port':
        beam_dx = hdg_y
        beam_dy = -hdg_x
    else:
        raise Exception('Unknown direction')

    # Make a unit vector
    mag = np.linalg.norm((beam_dx, beam_dy))
    beam_dx = beam_dx / mag
    beam_dy = beam_dy / mag
    return (beam_dx, beam_dy)

def ray_depth(bathy_grid, beam_angle, x0, y0, beam_dx, beam_dy, resolution):
    """Traces a beam to the bottom of a bathymetric depth grid given in bathy_grid
    Arguments
    ---------
    bathy_grid - The depth grid, instance of BathyGrid
    beam_angle - Beam angle in degrees
    x0, y0 - Launch position
    beam_dx, beam_dy - Unit vector representing top down launch angle of beam
    resolution - Step size to use while solving

    Returns tuple of (x, y, z) intersection of beam with the seafloor
    """
    # No need to trace straight down
    if beam_angle == 0:
        return (x0, y0, bathy_grid.get_depth(x0, y0))

    ba_rad = np.radians(beam_angle)
    ray_z = 0
    ray_x = x0
    ray_y = y0
    while ray_z < bathy_grid.get_depth(ray_x, ray_y):
        ray_z = ray_z + np.cos(ba_rad) * resolution
        ray_x = ray_x + beam_dx * np.sin(ba_rad) * resolution
        ray_y = ray_y + beam_dy * np.sin(ba_rad) * resolution

    return (ray_x, ray_y, bathy_grid.get_depth(ray_x, ray_y))

def width_from_depth(beam_angle, depth):
    """Gets swath width at a beam angle from a depth
    Arguments
    ---------
    beam_angle in degrees
    depth in meters (or whatever)

    Returns width to one side of the swath
    """
    beam_angle = np.radians(np.abs(beam_angle))
    return np.tan(beam_angle) * depth