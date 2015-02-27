"""
Functions to trace a beam (ray) from a sonar system to an arbitrary seafloor
defined by a grid of depths

Damian Manda
8 Feb 2015
"""

import numpy as np
#def unit_vector(vector)

# beam_dx = +-hdg_dy
# beam_dy = -+hdg_dx
def hdg_to_beam(hdg_x, hdg_y, direction='stbd'):
    """Given a heading vector, converts this to a beam pointing direction of a
    sonar that has a swath perpendicular to the direction of travel.

    Arguments
    ---------
    hdg_x, hdg_y - Heading vector components
    dir - side to project ('port' or 'stbd')

    Returns unit vector of beam direction on desired side
    """
    # Switch these to go from left handed to right handed coord.
    if direction == 'stbd':
        beam_dx = hdg_y
        beam_dy = -hdg_x
    elif direction == 'port':
        beam_dx = -hdg_y
        beam_dy = hdg_x
    else:
        raise Exception('Unknown direction')

    # Make a unit vector
    mag = np.linalg.norm((beam_dx, beam_dy))
    beam_dx = beam_dx / mag
    beam_dy = beam_dy / mag
    return (beam_dx, beam_dy)

def ray_depth(bathy_grid, beam_angle, x0, y0, beam_dx, beam_dy, resolution, \
    seed_depth=0):
    """Traces a beam to the bottom of a bathymetric depth grid given in bathy_grid
    Arguments
    ---------
    bathy_grid - The depth grid, instance of BathyGrid
    beam_angle - Beam angle in degrees
    x0, y0 - Launch position
    beam_dx, beam_dy - Unit vector representing top down launch angle of beam
    resolution - Step size to use while solving
    seed_depth = depth at which to start tracing

    Returns tuple of (x, y, z) intersection of beam with the seafloor
    """
    # No need to trace straight down
    if beam_angle == 0:
        return (x0, y0, bathy_grid.get_depth(x0, y0))

    ba_rad = np.radians(beam_angle)
    ray_z = float(seed_depth)
    if seed_depth != 0:
        beam_len = ray_z / np.cos(ba_rad)
        ray_x = x0 + beam_dx * np.sin(ba_rad) * beam_len
        ray_y = y0 + beam_dy * np.sin(ba_rad) * beam_len
    else:
        ray_x = x0
        ray_y = y0

    # Trace downward
    while ray_z < bathy_grid.get_depth(ray_x, ray_y):
        ray_z = ray_z + np.cos(ba_rad) * resolution
        ray_x = ray_x + beam_dx * np.sin(ba_rad) * resolution
        ray_y = ray_y + beam_dy * np.sin(ba_rad) * resolution
    
    # Trace upward if needed
    if seed_depth != 0 and abs(ray_z - bathy_grid.get_depth(ray_x, ray_y)) > \
        (np.cos(ba_rad) * resolution * 1.5):
        while ray_z > bathy_grid.get_depth(ray_x, ray_y):
                ray_z = ray_z - np.cos(ba_rad) * resolution
                ray_x = ray_x - beam_dx * np.sin(ba_rad) * resolution
                ray_y = ray_y - beam_dy * np.sin(ba_rad) * resolution

    return (ray_x, ray_y, bathy_grid.get_depth(ray_x, ray_y))

def width_from_depth(beam_angle, depth):
    """Gets swath width at a beam angle from a depth
    Arguments
    ---------
    beam_angle in degrees
    depth in meters (or whatever)

    Returns width to one side of the swath
    """
    beam_angle_rad = np.radians(np.abs(beam_angle))
    return np.tan(beam_angle_rad) * depth

def beam_len_from_depth(beam_angle, depth):
    """Get the length of the beam ray for a depth

    Arguments
    ---------
    beam_angle in degrees
    depth in meters (or whatever)
    """
    beam_angle_rad = np.radians(np.abs(beam_angle))
    return np.cos(beam_angle_rad) / depth

