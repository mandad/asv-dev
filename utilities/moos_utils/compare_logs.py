import slog_graph
import argparse
import numpy as np
from scipy import signal
import matplotlib
import matplotlib.pyplot as plt
import pdb

log_graphs = []
colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
colors = ['#0072bd', '#d95319', '#edb120', '#7e2f8e', '#77ac30', '#4dbeee', '#a2142f']
# Hack to make a single graph a different color
#colors = ['g', 'r', 'c', 'm', 'y', 'k', 'b']
styles = ['-', '--', '-.', ':']

def compare_logs(filenames, cols, min_time = 0, max_time = None, \
    secondary_cols = None, ylabel = None, lw = [1.0], style_os = 0, diff=False, 
    fft=False, legend = None, color_os=0, ylabel2=None):
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
        if len(lw) == 1:
            lw = np.ones(len(secondary_cols) + len(cols)) * lw
    # It will still be 1 if secondary_cols is None
    if len(lw) == 1:
        lw = np.ones(len(cols)) * lw
    

    for i in range(len(log_graphs)):
        col_ind = 0;
        if diff:
            if len(cols) < 2:
                print("Error: Can only do a difference with two columns.")
                return
            label_text = log_graphs[i].headings[cols[0]] +  " - " + \
                log_graphs[i].headings[cols[1]]
            ax1.plot(log_graphs[i].get_col_data(0), log_graphs[i].get_col_data(cols[0]) \
                - log_graphs[i].get_col_data(cols[1]), \
                color=colors[color_os], linestyle=styles[i+style_os], lw=lw[0], \
                label=label_text)
            # Advance the counters so we can plot more if needed
            cols_arr = cols_arr[2:]
            col_ind = 2
        if fft:
            if len(cols) > 1:
                print("Error: Can only do an fft with one column.")
                return
            fs = 10
            for_spectrum = log_graphs[i].get_col_data(cols[0])
            # The fields are usually nan in the beginning, this must be removed
            # to compute the spectrum
            for_spectrum = for_spectrum[~np.isnan(for_spectrum)]
            f, Pwelch_spec = signal.welch(for_spectrum, fs, \
                nperseg=512, scaling='density')
            label_text = "Spectrum of " + log_graphs[i].headings[cols[0]]
            ax1.semilogy(f, Pwelch_spec, lw=lw[0], label=label_text, \
                color=colors[color_os], linestyle=styles[i+style_os],)
        else:
            for col in cols_arr:
                ax1.plot(log_graphs[i].get_col_data(0), log_graphs[i].get_col_data(col), \
                    color=colors[(col_ind + color_os) % len(colors)], linestyle=styles[i+style_os], \
                    lw=lw[col_ind], label=log_graphs[i].headings[col])
                col_ind = (col_ind + 1)
            if secondary_cols is not None:
                for col in secondary_cols:
                    ax2.plot(log_graphs[i].get_col_data(0), \
                        log_graphs[i].get_col_data(col), \
                        color=colors[(col_ind + color_os) % len(colors)], \
                        linestyle=styles[i+style_os], lw=lw[col_ind], \
                        label=log_graphs[i].headings[col])
                    col_ind = (col_ind + 1)
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
    if legend is not None:
        labels = legend.split("|")
    leg = plt.legend(handles, labels, shadow=True, fancybox=True, loc='best') #'best'
    ltext  = leg.get_texts()
    if not fft:
        ax1.set_xlabel('Time [s]')
        if ylabel is not None:
            ax1.set_ylabel(ylabel)
        if ylabel2 is not None:
            ax2.set_ylabel(ylabel2, rotation=270, labelpad=15)
    else:
        plt.xlabel('frequency [Hz]')
        plt.ylabel('PSD [ROT^2/Hz]')
    plt.setp(ltext, fontsize=14)
    if min_time > 0 and max_time is not None:
        plt.xlim([min_time, max_time])
    #plt.ylim([0, 90])
    matplotlib.rcParams.update({'font.size': 14})
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
    parser.add_argument('--ylabel2')
    parser.add_argument('--lw', nargs='*', type=float, default=[1.0])
    parser.add_argument('--style_os', type=int, default=0)
    parser.add_argument('--color_os', type=int, default=0)
    parser.add_argument('--diff', action="store_true")
    parser.add_argument('--fft', action="store_true")
    parser.add_argument('--legend')
    args = parser.parse_args()
    # if args.max_time is not None:
    compare_logs(args.filenames, args.cols, args.min_time, args.max_time, \
        args.sec_cols, args.ylabel, args.lw, args.style_os, args.diff, args.fft,
        args.legend, args.color_os, args.ylabel2)
    # else:
    #     compare_logs(args.filenames, args.cols, args.min_time)

if __name__ == '__main__':
    main()