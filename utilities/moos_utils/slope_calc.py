import slog_graph
import numpy as np
import matplotlib.pyplot as plt

time_len = 3 #seconds
filter_len = 10 * time_len

slog_rough = slog_graph.SLogGraph("MOOSLog_14_1_2016_____20_48_37.slog")
speeds_rough = slog_rough.get_col_data(16)
slopes_rough = [(speeds_rough[x] - speeds_rough[x-filter_len])/(filter_len/time_len) \
    for x in np.arange(speeds_rough.size-filter_len)+filter_len]
slopes_rough=np.append(np.zeros(filter_len),slopes_rough)

plt.plot(slopes_rough); plt.plot(speeds_rough); plt.show()