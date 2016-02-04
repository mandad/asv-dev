import slog_graph
import numpy as np
import matplotlib.pyplot as plt

filter_len = 30;

slog_rough = slog_graph.SLogGraph("MOOSLog_14_1_2016_____20_48_37.slog")
speeds_rough = slog_rough.get_col_data(16)
slopes_rough = [(speeds_rough[x] - speeds_rough[x-filter_len])/(filter_len/3) \
    for x in np.arange(speeds_rough.size-filter_len)+filter_len]
slopes_rough=np.append(np.zeros(filter_len),slopes_rough)

plt.plot(slopes_rough); plt.plot(speeds_rough); plt.show()