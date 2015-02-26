"""
Generates a bathymetric grid using parameters
Allows arbitrary size and resolution regular grids to be created

Damian Manda
8 Feb 2015
"""

import numpy as np
import rasterio
try:
    from mayavi import mlab
except:
    has_mlab = False
else:
    has_mlab = True
# has_mlab = False

import matplotlib.pyplot as plt

class BathyGrid(object):
    def __init__(self, size_x, size_y, res, geo_transform=None):
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

    def generate_x_hole(self, deep, shallow):
        self.generate_dip(deep, shallow, 'y')
        grid_temp = np.array(self.grid, copy=True)
        self.generate_dip(deep, shallow, 'x')
        self.grid = (grid_temp + self.grid) / 2
        # or
        # self.grid = np.sqrt(grid_temp * self.grid)

    def generate_x_bump(self, deep, shallow):
        self.generate_x_hole(deep, shallow)
        self.grid = (-1 * self.grid) + (shallow + deep)

    def generate_x(self, deep, shallow):
        self.generate_dip(deep, shallow, 'y')
        grid_temp = np.array(self.grid, copy=True)
        self.generate_dip(deep, shallow, 'x')
        self.grid = np.maximum(self.grid, grid_temp)

    def generate_hole(self, deep, shallow):
        self.grid = self.make_gaussian(self.size_x, self.size_x / 3)
        self.grid = shallow + (self.grid * ((deep-shallow) / np.max(self.grid)))

    def generate_bump(self, deep, shallow):
        self.generate_hole(shallow, deep)

    @classmethod
    def from_bathymetry(cls, file, depth_pos=False):
        grid_file = rasterio.open('terrain/Flat_Region.tif', 'r')
        # to get pixels, mx, my are in map units
        dimensions = grid_file.shape
        resolution = round(max(grid_file.res))
        config_cls = cls(dimensions[0], dimensions[1], resolution, grid_file.get_transform())

    def bathymetry_file(self):
        pass

    @staticmethod
    def make_gaussian(size, fwhm = 3, center=None):
        """ Make a square gaussian kernel.

        size is the length of a side of the square
        fwhm is full-width-half-maximum, which
        can be thought of as an effective radius.
        """
     
        x = np.arange(0, size, 1, float)
        y = x[:,np.newaxis]
        
        if center is None:
            x0 = y0 = size // 2
        else:
            x0 = center[0]
            y0 = center[1]
        
        return np.exp(-4*np.log(2) * ((x-x0)**2 + (y-y0)**2) / fwhm**2)

    def disp_grid(self, view_3D=True):
        if self.grid is not None:
            if has_mlab and view_3D:
                mlab.surf(-self.grid, colormap='jet', warp_scale='20')
            else:
                plt.imshow(-np.transpose(self.grid), cmap='jet')
                plt.colorbar()
                plt.show()
        else:
            raise Exception('No grid has been generated')

    def get_depth(self, x, y):
        if self.grid is None:
            raise Exception('No grid has been generated')
        if self.geo_transform is not None:
            px = int((mx - gt[0]) / gt[1])
            py = int((my - gt[3]) / gt[5])
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
