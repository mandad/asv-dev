import slog_graph
import argparse
import numpy as np
import matplotlib.pyplot as plt
import pdb

log_graphs = []
colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
# Hack to make a single graph a different color
#colors = ['g', 'r', 'c', 'm', 'y', 'k', 'b']
styles = ['-', '--', '-.', ':']

def compare_logs(filenames, cols, min_time = 0, max_time = None, \
    secondary_cols = None, ylabel = None, lw = 1.0, style_os = 0, diff=False):
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
    plt.figure(num=1, figsize=(17,10))
    ax1 = plt.gca()
    if secondary_cols is not None:
        ax2 = ax1.twinx()
        sec_cols_arr = np.array(secondary_cols)

    for i in range(len(log_graphs)):
        color_ind = 0;
        if diff:
            if len(cols) != 2:
                print("Error: Can only do a difference with two columns.")
                return
            label_text = log_graphs[i].headings[cols[0]] +  " - " + \
                log_graphs[i].headings[cols[1]]
            ax1.plot(log_graphs[i].get_col_data(0), log_graphs[i].get_col_data(cols[0]) \
                - log_graphs[i].get_col_data(cols[1]), \
                color=colors[color_ind], linestyle=styles[i+style_os], lw=lw, \
                label=label_text)
        else:
            for col in cols_arr:
                ax1.plot(log_graphs[i].get_col_data(0), log_graphs[i].get_col_data(col), \
                    color=colors[color_ind], linestyle=styles[i+style_os], lw=lw, \
                    label=log_graphs[i].headings[col])
                color_ind = (color_ind + 1) % len(colors)
            if secondary_cols is not None:
                for col in secondary_cols:
                    ax2.plot(log_graphs[i].get_col_data(0), \
                        log_graphs[i].get_col_data(col), color=colors[color_ind], \
                        linestyle=styles[i+style_os], lw=lw, label=log_graphs[i].headings[col])
                    color_ind = (color_ind + 1) % len(colors)
        #add_file_to_plot(i, cols_arr)

    # Format the plot
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
    ax1.set_xlabel('Time [s]')
    if ylabel is not None:
        ax1.set_ylabel(ylabel)
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
    parser.add_argument('--ylabel')
    parser.add_argument('--lw', type=float, default=1.0)
    parser.add_argument('--style_os', type=int, default=0)
    parser.add_argument('--diff', action="store_true")
    args = parser.parse_args()
    # if args.max_time is not None:
    compare_logs(args.filenames, args.cols, args.min_time, args.max_time, \
        args.sec_cols, args.ylabel, args.lw, args.style_os, args.diff)
    # else:
    #     compare_logs(args.filenames, args.cols, args.min_time)

if __name__ == '__main__':
    main()