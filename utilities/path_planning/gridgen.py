"""
Generates a bathymetric grid using parameters
Allows arbitrary size and resolution regular grids to be created

Damian Manda
8 Feb 2015
"""

import numpy as np
try:
    from mayavi import mlab
except:
    has_mlab = False
else:
    has_mlab = True

# has_mlab = False

import matplotlib.pyplot as plt

class BathyGrid(object):
    def __init__(self, size_x, size_y, res):
        self.grid = None
        self.size_x = size_x
        self.size_y = size_y
        self.resolution = res

        self.index_x = np.linspace(0, size_x * res, size_x)
        self.index_y = np.linspace(0, size_y * res, size_y)

    def generate_slope(self, min, max):
        if max < min:
            raise Exception('Maximum depth specified less than minumum.')
        y_comp = np.linspace(max, min, self.size_y)
        x_comp = np.zeros(self.size_x)
        # 'ij' indexing means yv[x,y]
        xv, self.grid = np.meshgrid(x_comp, y_comp, indexing='ij')

    def generate_flat(self, depth):
        self.grid = np.full((self.size_x, self.size_y), depth)

    def generate_hump(self, deep, shallow, direction='y'):
        self.generate_linear_bump(deep, shallow, 'up', direction)

    def generate_dip(self, deep, shallow, direction='y'):
        self.generate_linear_bump(shallow, deep, 'up', direction)

    def generate_linear_bump(self, deep, shallow, vert_dir='up', orientation='y'):
        # Create a gaussian in the desired direction
        if orientation == 'y':
            axis_size = self.size_y
        else:
            axis_size = self.size_x
        v_pts = np.arange(axis_size, dtype=np.float)
        mu = axis_size / 2
        sigma = axis_size / 10
        v_comp = 1/(sigma * np.sqrt(2 * np.pi)) * np.exp(-(v_pts - mu)**2 / (2 * sigma**2))

        # compensate to desired depths
        if (vert_dir == 'up'):
            v_comp = v_comp * ((shallow-deep) / np.max(v_comp)) + deep
        else:
            v_comp = deep - (v_comp * ((shallow-deep) / np.max(v_comp)))

        print('axis_size: {0}, v_comp: {1}'.format(axis_size, len(v_comp)))
        if orientation == 'y':
            self.grid = np.tile(v_comp.reshape(axis_size, 1), (1, self.size_y))
        else:
            self.grid = np.tile(v_comp.reshape(1, axis_size), (self.size_x, 1))

    def generate_hole():
        pass

    def disp_grid(self):
        if self.grid is not None:
            if has_mlab:
                mlab.surf(-self.grid, colormap='jet', warp_scale='20')
            else:
                plt.imshow(self.grid, cmap='jet')
                plt.colorbar()
                plt.show()
        else:
            raise Exception('No grid has been generated')

    def get_depth(self, x, y):
        if self.grid is None:
            raise Exception('No grid has been generated')
        x_idx = self.find_nearest(self.index_x, x)
        y_idx = self.find_nearest(self.index_y, y)
        # Could interpolate or something if wanted to get fancy
        return self.grid[x_idx, y_idx]

    @staticmethod
    def find_nearest(array, value):
        """Returns the index of the value nearest to the input in array
        """
        idx = (np.abs(array-value)).argmin()
        return idx
