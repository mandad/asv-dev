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
import pdb
import matplotlib.pyplot as plt

class BathyGrid(object):
    def __init__(self, size_x, size_y, res, geo_transform=None):
        self.grid = None
        self.size_x = size_x
        self.size_y = size_y
        self.resolution = res
        self.geo_transform = geo_transform
        self.imported = False
        self.grid_mean = 0

        if geo_transform is not None:
            start_x = geo_transform[0]
            start_y = geo_transform[3]
            y_dir = geo_transform[5]
            x_dir = geo_transform[1]
        else:
            self.geo_transform = [0, res, 0, 0, 0, res]
            start_x = 0
            start_y = 0
            y_dir = 1
            x_dir = 1

        self.index_x = np.linspace(start_x, start_x + size_x * res * x_dir, size_x)
        self.index_y = np.linspace(start_y, start_y + size_y * res * y_dir, size_y)

    @classmethod
    def from_bathymetry(cls, filename, depth_pos=False):
        grid_file = rasterio.open(filename, 'r')
        # to get pixels, mx, my are in map units
        dimensions = grid_file.shape
        resolution = round(max(grid_file.res))
        config_cls = cls(dimensions[1], dimensions[0], resolution, grid_file.get_transform())
        config_cls.pregenerated_grid(grid_file.read_band(1), depth_pos)
        grid_file.close()
        return config_cls

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

    def pregenerated_grid(self, grid, depth_pos):
        if depth_pos:
            self.grid = grid
        else:
            self.grid = -grid
        self.imported = True
        self.calc_grid_mean()

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

    def disp_grid(self, view_3D=True, existing_fig=False):
        if self.grid is not None:
            if has_mlab and view_3D:
                mlab.surf(-self.grid, colormap='jet', warp_scale='20')
            else:
                if self.imported:
                    plt.imshow(-self.grid, cmap='jet', zorder=0, \
                        extent=self.get_extents())
                else:
                    plt.imshow(-np.transpose(self.grid), cmap='jet', zorder=0, \
                        extent=self.get_extents())
                plt.colorbar()
                if not existing_fig:
                    plt.show()
        else:
            raise Exception('No grid has been generated')

    def avg_aspect(self):
        """http://blog.perrygeo.net/2012/03/18/average-aspect/
        http://geoexamples.blogspot.com/2014/03/shaded-relief-images-using-gdal-python.html
        """
        x, y = np.gradient(self.grid)
        hyp = np.sqrt(x**2 + y**2)
        return np.degrees(np.arctan2(np.sum(y/hyp), np.sum(-x/hyp)))

    def avg_slope(self):
        x, y = np.gradient(self.grid)
        slope = np.pi/2. - np.arctan(np.sqrt(x**2 + y**2))
        return np.average(slope)

    def get_depth(self, x, y):
        """Get the depth from the grid at a specified x,y point which does not
        necessarily correspond to the size of the grid"""
        if self.grid is None:
            raise Exception('No grid has been generated')

        # x_idx = self.find_nearest(self.index_x, x)
        # y_idx = self.find_nearest(self.index_y, y)

        # Translate locations to indicies
        x_idx = np.clip(int((x - self.geo_transform[0]) / self.geo_transform[1]), \
            0, self.size_x - 1)
        y_idx = np.clip(int((y - self.geo_transform[3]) / self.geo_transform[5]), \
            0, self.size_y - 1)

        # Could interpolate or something if wanted to get fancy
        if self.imported:
            depth_val = self.grid[y_idx, x_idx]
            if depth_val is np.ma.masked:
                depth_val = self.grid_mean
        else:
            depth_val = self.grid[x_idx, y_idx]

        # pdb.set_trace()
        return depth_val

    def get_extents(self):
        """Return extents in [left, right, bottom, top]
        minx = gt[0]
        miny = gt[3] + width*gt[4] + height*gt[5] 
        maxx = gt[0] + width*gt[1] + height*gt[2]
        maxy = gt[3]

        Corner Coordinates:
        Upper Left  (  359078.849, 4763674.826) ( 70d43'45.31"W, 43d 0'45.68"N)
        Lower Left  (  359078.849, 4762415.826) ( 70d43'44.17"W, 43d 0' 4.89"N)
        Upper Right (  360396.849, 4763674.826) ( 70d42'47.12"W, 43d 0'46.56"N)
        Lower Right (  360396.849, 4762415.826) ( 70d42'45.98"W, 43d 0' 5.76"N)
        Center      (  359737.849, 4763045.326) ( 70d43'15.65"W, 43d 0'25.72"N)

        output from this:
        [359078.84858129267, 360337.84858129267, 4762356.826454721, 4763674.826454721]
        [359078.84858129267, 360396.84858129267, 4762415.826454721, 4763674.826454721]
        """
        left = self.geo_transform[0]
        right = self.geo_transform[0] + self.size_x *  self.geo_transform[1]
        if self.imported:
            top = self.geo_transform[3]
            bottom = self.geo_transform[3] + self.size_y * self.geo_transform[5]
        else:
            bottom = self.geo_transform[3]
            top = self.geo_transform[3] + self.size_y * self.resolution * self.geo_transform[5]

        return [left, right, bottom, top]

    def calc_grid_mean(self):
        if self.grid is not None:
            self.grid_mean = np.mean(self.grid)

    @staticmethod
    def find_nearest(array, value):
        """Returns the index of the value nearest to the input in array
        """
        idx = (np.abs(array-value)).argmin()
        return idx
