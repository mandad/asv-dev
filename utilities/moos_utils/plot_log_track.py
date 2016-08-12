import numpy as np
import matplotlib.pyplot as plt
import matplotlib
#import tiff_convert

xlog = np.genfromtxt('NAV_X.klog')
xcoord = xlog[:,3]
ylog = np.genfromtxt('NAV_Y.klog')
ycoord = ylog[:,3]

# Format the plot
#plt.plot(xcoord, ycoord)
fig = plt.figure(figsize=(12,8))
ax = fig.add_subplot(111, aspect='equal') 
ax.get_xaxis().set_ticks([])
ax.get_yaxis().set_ticks([])
ax.set_axis_off()
ax.plot(xcoord, ycoord)

# Save / Show map image
fig.savefig('NAV_Plot.png', dpi=600, bbox_inches='tight', pad_inches=0)
#tiff_convert.ConvertToGTiff(save_name, xlim_data, ylim_data, utm_zone)