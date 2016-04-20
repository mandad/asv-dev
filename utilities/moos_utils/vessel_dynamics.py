import argparse
import pdb
import slog_graph
import numpy as np

def print_info(log, time_range):
    log.set_time_range(time_range)
    thrust = np.mean(log.get_col_data(18))
    rudder = np.mean(log.get_col_data(4))
    avg_rot = np.mean(log.get_col_data(2))
    avg_speed = np.mean(log.get_col_data(16))
    print("ROT: {:.3f}, Speed: {:.3f}".format(avg_rot, avg_speed))
    print("{:.0f}\t{:.0f}\t{:.3f}\t{:.3f}".format(thrust, rudder, avg_rot, avg_speed))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    parser.add_argument('start_time', type=float)
    parser.add_argument('end_time', type=float)
    args = parser.parse_args()

    time_range = (args.start_time, args.end_time)
    log = slog_graph.SLogGraph(args.filename)

    #pdb.set_trace()

    print_info(log, time_range)


if __name__ == '__main__':
    main()