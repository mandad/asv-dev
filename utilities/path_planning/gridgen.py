"""
Generates a bathymetric grid using parameters
Allows arbitrary size and resolution regular grids to be created

Damian Manda
2/8/2015
"""

import numpy as np
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
        y_comp = np.linspace(max, min, self.size_y)
        x_comp = np.zeros(self.size_x)
        # 'ij' indexing means yv[x,y]
        xv, self.grid = np.meshgrid(x_comp, y_comp, indexing='ij')

    def generate_flat(self, depth):
        self.grid = np.full((self.size_x, self.size_y), depth)

    def generate_hump(self, deep, shallow, direction='y'):
        # Create a gaussian in the desired direction
        raise NotImplementedError()

    def disp_grid(self):
        if self.grid is not None:
            plt.imshow(self.grid, cmap='jet')
            plt.colorbar()
            plt.show()

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
