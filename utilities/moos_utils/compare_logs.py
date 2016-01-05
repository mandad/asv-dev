import slog_graph
import argparse
import numpy as np
import matplotlib.pyplot as plt
import pdb

log_graphs = []

def compare_logs(filenames, cols):
    cols_arr = np.array(cols)
    for f in filenames:
        this_log = slog_graph.SLogGraph(f)
        log_graphs.append(this_log)

    # pdb.set_trace()
    for i in range(len(log_graphs)):
        plt.plot(log_graphs[i].get_col_data(0), log_graphs[i].get_col_data(cols_arr))
        #add_file_to_plot(i, cols_arr)

    # Format the plot
    plt.xlabel('Time [s]')
    leg = plt.legend(np.tile(log_graphs[0].headings[cols_arr],len(filenames)), shadow=True, \
        fancybox=True, loc='best')
    ltext  = leg.get_texts()
    plt.setp(ltext, fontsize='small')
    plt.show()

def add_file_to_plot(index, cols):
    pass 
    

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='+')
    parser.add_argument('--cols', nargs='*', type=int)
    parser.add_argument('--min_time', type=float)
    args = parser.parse_args()
    compare_logs(args.filenames, args.cols)

if __name__ == '__main__':
    main()