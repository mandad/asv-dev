import slog_graph
import argparse
import numpy as np
import matplotlib.pyplot as plt
import pdb

log_graphs = []
colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
styles = ['-', '--', '-.', ':']

def compare_logs(filenames, cols, min_time = 0, max_time = None, secondary_cols = None):
    cols_arr = np.array(cols)
    # Open the files
    for f in filenames:
        this_log = slog_graph.SLogGraph(f)
        if min_time > 0:
            this_log.set_min_time(min_time)
        if max_time is not None:
            this_log.set_max_time(max_time)
        log_graphs.append(this_log)

    # Make the plots
    ax1 = plt.gca()
    if secondary_cols is not None:
        ax2 = ax1.twinx()
        sec_cols_arr = np.array(secondary_cols)

    for i in range(len(log_graphs)):
        color_ind = 0;
        for col in cols_arr:
            ax1.plot(log_graphs[i].get_col_data(0), log_graphs[i].get_col_data(col), \
                color=colors[color_ind], linestyle=styles[i], \
                label=log_graphs[i].headings[col])
            color_ind = (color_ind + 1) % len(colors)
        if secondary_cols is not None:
            for col in secondary_cols:
                ax2.plot(log_graphs[i].get_col_data(0), \
                    log_graphs[i].get_col_data(col), color=colors[color_ind], \
                    linestyle=styles[i],label=log_graphs[i].headings[col])
                color_ind = (color_ind + 1) % len(colors)
        #add_file_to_plot(i, cols_arr)

    # Format the plot
    plt.xlabel('Time [s]')
    handles, labels = ax1.get_legend_handles_labels()
    if secondary_cols is not None:
        all_plot_cols = np.append(cols_arr, secondary_cols)
        h2, l2 = ax2.get_legend_handles_labels()
        handles = handles + h2
        labels = labels + l2
    else:
        all_plot_cols = cols_arr
    leg = plt.legend(handles, labels, shadow=True, fancybox=True, loc='best')
    ltext  = leg.get_texts()
    plt.setp(ltext, fontsize='small')
    plt.show()

def add_file_to_plot(index, cols):
    pass 
    

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='+')
    parser.add_argument('--cols', nargs='*', type=int)
    parser.add_argument('--sec_cols', nargs='*', type=int)
    parser.add_argument('--min_time', type=float, default=0)
    parser.add_argument('--max_time', type=float)
    args = parser.parse_args()
    # if args.max_time is not None:
    compare_logs(args.filenames, args.cols, args.min_time, args.max_time, args.sec_cols)
    # else:
    #     compare_logs(args.filenames, args.cols, args.min_time)

if __name__ == '__main__':
    main()