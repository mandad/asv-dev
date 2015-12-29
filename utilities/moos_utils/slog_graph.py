import numpy as np
import matplotlib.pyplot as plt
import argparse

class SLogGraph(object):
    def __init__(self, filename):
        self.num_data = 0
        self.initialized = False
        self.headings = []
        self.valid_data = False
        self.min_time = 0
        self.min_index = 0

        if filename is not None:
            self.filename = filename
            self.parse_file()

    def open_file(self):
        try:
            self.log_file = open(self.filename, 'r')
        except Exception, e:
            print("Error opening file: " + self.filename)
            return False
        return True

    def parse_file(self):
        if not self.open_file():
            return

        prev_line = []
        prev2_line = []
        fields = []
        
        # Do this so we can preallocate the array of data
        # for num_rows, l in enumerate(self.log_file):
        #     pass
        # num_rows = num_rows + 1
        # self.log_file.seek(0)

        for line in self.log_file:
            fields = line.split()
            if fields[0] != '%%' and len(fields) > 1:
                break
            prev2_line = prev_line
            prev_line = fields

        self.headings = np.array(prev2_line[1:])
        self.num_cols = len(self.headings)

        self.log_file.close()

        self.data = np.genfromtxt(self.filename, comments="%", delimiter=None, \
            missing_values='NaN')
        self.valid_data = True

    # Not needed, the numpy genfromtxt does this
    def add_row(self, data_row, data_array):
        new_row = np.empty(len(data_row))
        for i, num in enumerate(data_row):
            if num == 'NaN':
                new_row[i] = np.nan
            else:
                new_row[i] = float(num)
        data_array.append(new_row)

        return data_array

    def plot_all_data(self):
        if self.valid_data:
            plt.plot(self.data[self.min_index:,0], self.data[self.min_index:,1:])
            plt.xlabel('Time [s]')
            leg = plt.legend(self.headings[1:], shadow=True, fancybox=True, \
                loc='best')
            ltext  = leg.get_texts()
            plt.setp(ltext, fontsize='small')
            plt.show()

    def plot_cols(self, columns_to_plot):
        if len(columns_to_plot) > 0 and self.valid_data:
            plt.plot(self.data[self.min_index:,0], self.data[self.min_index:,columns_to_plot])
            plt.xlabel('Time [s]')
            leg = plt.legend(self.headings[columns_to_plot], shadow=True, \
                fancybox=True, loc='best')
            ltext  = leg.get_texts()
            plt.setp(ltext, fontsize='small')
            plt.show()

    def list_cols(self):
        if self.valid_data:
            for i, header in enumerate(self.headings):
                print('{:>2} '.format(i) + header)

    def get_col_data(self, cols):
        if self.valid_data:
            return self.data[self.min_index:,cols]
        return None

    def set_min_time(self, min_time):
        self.min_time = min_time
        if self.valid_data:
            self.min_index = np.argmax(self.data[:,0]>min_time) - 1
            return True
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    args = parser.parse_args()
    log_graph = SLogGraph(args.filename)
    if log_graph.valid_data:
        log_graph.plot_all_data()

if __name__ == '__main__':
    main()