import pymoos
import time
# import numpy as np
import math
import pdb
import sys

TURN_PT_OFFSET = 15
ALIGNMENT_LINE_LEN = 10

def magnitude(v):
    return math.sqrt(sum(v[i]*v[i] for i in range(len(v))))

def unit_vector(vector):
    vmag = magnitude(vector)
    return [ vector[i]/vmag  for i in range(len(vector)) ]

class SurveyLine(object):
    def __init__(self):
        self.points = list()
        self.alignment_line = list()
        self.turn_point = list()
        self.line_num = None

    def add_vertex(self, x, y):
        self.points.append((x,y))

    def reverse_line(self):
        self.points.reverse()

    def end_line(self):
        self.calculate_alignment_line()
        self.calclulate_turn_pt()

    def set_line_num(self, num):
        self.line_num = num

    def calculate_alignment_line(self):
        if len(self.points) >= 2:
            start_heading = (self.points[0][0] - self.points[1][0], \
                self.points[0][1] - self.points[1][1])
            start_heading = unit_vector(start_heading)
            # actually only one point
            self.alignment_line.append( (self.points[0][0] + start_heading[0] * ALIGNMENT_LINE_LEN, \
                self.points[0][1] + start_heading[1] * ALIGNMENT_LINE_LEN) )

    def calclulate_turn_pt(self):
        if len(self.points) >= 2:
            end_heading = (self.points[-1][0] - self.points[-2][0], \
                self.points[-1][1] - self.points[-2][1])
            end_heading = unit_vector(end_heading)
            self.turn_point.append( (self.points[-1][0] + end_heading[0] * TURN_PT_OFFSET, \
                self.points[-1][1] + end_heading[1] * TURN_PT_OFFSET) )

    def get_points_string(self):
        full_points = self.alignment_line + self.points + self.turn_point
        
        # full_points.extend(self.alignment_line)
        # full_points.extend(self.points)
        # full_points.extend(self.turn_point)

        point_list = ['{0:.2f},{1:.2f}:'.format(pt[0], pt[1]) for pt in full_points]

        points_message = ''.join(point_list)
        # pdb.set_trace()
        # self.path_message = 'points=' + points_message[:-1]
        return points_message[:-1]

class HypackLineReader(object):
    def __init__(self, line_file):
        self.line_file = line_file
        self.num_lines = 0
        self.lines = list()

    def read_file(self):
        f = open(self.line_file, 'r')
        num_cur_line_pts = 2
        cur_line = SurveyLine();
        line_num = 0

        for line in f:
            split_line = line.split()
            if len(split_line) > 0:
                if split_line[0] == 'LNS':
                    self.num_lines = int(split_line[1])
                elif split_line[0] == 'LIN':
                    # Start a new line
                    self.num_cur_line_pts = int(split_line[1])
                    cur_line = SurveyLine()
                elif split_line[0] == 'PTS':
                    cur_line.add_vertex(float(split_line[1]), \
                        float(split_line[2]))
                elif split_line[0] == 'LNN':
                    # This is the line number and has no meaning to us
                    cur_line.set_line_num(int(split_line[1]))
                elif split_line[0] == 'EOL':
                    line_num += 1
                    if line_num % 2 == 0:
                        cur_line.reverse_line()
                    cur_line.end_line()
                    self.lines.append(cur_line)

        f.close()

    def get_lines_msg(self):
        all_lines = [line.get_points_string() for line in self.lines]
        path_message = 'points=' + ':'.join(all_lines)
        return path_message
#====================================
# MOOS Comms

comms = pymoos.comms()
filename_hypack = ""

def on_connect():
    # line_reader = HypackLineReader(filename_hypack)
    # line_reader.read_file()
    # msg = line_reader.get_lines_msg()
    # print('Posting Message to MOOS')
    # print(msg)
    # comms.notify('UTM_SURVEYLINE', msg, pymoos.time())
    return True

def main(argv):
    comms.set_on_connect_callback(on_connect);
    # comms.run('192.168.2.3',9000,'pHypackPath')
    filename_hypack = argv[0]
    # comms.run('10.42.0.15',9000,'pHypackPath')
    print('Connecting to MOOSDB')
    comms.run('192.168.2.3',9000,'pHypackPath')
    if comms.wait_until_connected(2000):
        line_reader = HypackLineReader(filename_hypack)
        line_reader.read_file()
        msg = line_reader.get_lines_msg()
        print('Posting Message to MOOS')
        print(msg)
        comms.notify('UTM_SURVEYLINE', msg, pymoos.time())
    else:
        print('Timed out trying to send to survey system.')
    comms.close(True)


if __name__ == "__main__":
    main(sys.argv[1:])        
