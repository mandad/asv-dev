import pymoos
import time
import followpath
import pathplan
import pdb
from shapely.geometry import Polygon, MultiPoint, Point, MultiPolygon
import shapely.geometry
from shapely.prepared import prep

SWATH_INTERVAL = 15 #meters
NEXT_PATH_SIDE = ['port', 'stbd']
# 0 = port, 1 = stbd
FIRST_SWATH_SIDE = 1
DEBUG_MODE = False
# ALIGNMENT_LINE_LEN = 10
ALIGNMENT_LINE_LEN = 30
REMOVE_IN_COVERAGE = True

class RecordSwath(object):
    def __init__(self):
        self.comms = pymoos.comms()
        self.comms.set_on_connect_callback(self.connect_callback)
        self.comms.set_on_mail_callback(self.message_received)
        pymoos.set_moos_timewarp($(WARP))
        self.comms.set_comms_control_timewarp_scale_factor(0.4)
        self.comms.run('localhost', 9000, 'uRecordSwath')
        self.swath_record = dict()
        self.swath_record['port'] = followpath.RecordSwath(SWATH_INTERVAL)
        self.swath_record['stbd'] = followpath.RecordSwath(SWATH_INTERVAL)
        self.coverage = Polygon()

        # Initialize stored variables
        self.messages = dict()
        self.messages['SWATH_WIDTH'] = 0
        self.messages['NAV_X'] = 0
        self.messages['NAV_Y'] = 0
        self.messages['NAV_HEADING'] = 0
        self.messages['LINE_END'] = 0
        self.messages['LINE_BEGIN'] = 0
        self.messages['NEXT_SWATH_SIDE'] = 'port'
        self.messages['NEW_PATH'] = ''
        self.swath_side = 'port'
        self.next_swath_side = (FIRST_SWATH_SIDE + 1) % 2
        self.post_ready = False
        self.path_ready = False
        self.post_end = False
        self.path_message = ''
        self.outer_message = ''
        self.swath_record_message = ''
        self.start_line_message = ''
        self.recording = False  # this gets set when the line starts

    def connect_callback(self):
        result = True
        result = result and self.comms.register('SWATH_WIDTH', 0)
        # result = result and self.comms.register('NAV_X', 0)
        # result = result and self.comms.register('NAV_Y', 0)
        # result = result and self.comms.register('NAV_HEADING', 0)
        result = result and self.comms.register('LINE_END', 0)
        result = result and self.comms.register('LINE_BEGIN', 0)
        # result = result and self.comms.register('NEXT_SWATH_SIDE', 0)
        result = result and self.comms.register('NEW_PATH', 0)
        print('Swath recorder initialized')

        return result

    def message_received(self):
        try:
            for msg in self.comms.fetch():
                # Shouldn't ever be binary message
                # print 'Checking message type and getting message'
                if msg.is_double():
                    self.messages[msg.name()] = msg.double()
                else:
                    self.messages[msg.name()] = msg.string()

                if not DEBUG_MODE:
                    if msg.is_name('SWATH_WIDTH') and self.recording:
                        # Message in the format "x=10;y=10;hdg=150;port=52;stbd=37"
                        msg_parts = dict(item.split("=") for item in self.messages['SWATH_WIDTH'].split(";"))
                        # print "Received Swath Width {0}".format(split_msg)
                        # widths = split_msg.split('=')
                        # print msg_parts
                        self.swath_record['port'].record(float(msg_parts['port']), \
                            float(msg_parts['x']), float(msg_parts['y']), \
                            float(msg_parts['hdg']))
                        self.swath_record['stbd'].record(float(msg_parts['stbd']), \
                            float(msg_parts['x']), float(msg_parts['y']), \
                            float(msg_parts['hdg']))

                    if msg.is_name('LINE_BEGIN'):
                        print '\n**** Line beginning, starting to record swath ****'
                        self.recording = True

                    if msg.is_name('LINE_END'):
                        self.recording = False
                        # Publish swath generation side, and trigger pPathPlan
                        self.next_swath_side += 1
                        self.swath_side = NEXT_PATH_SIDE[self.next_swath_side % 2]
                        print 'End of Line, outputting swath points on ' + self.swath_side + ' side.'

                        # Record the last point
                        # pdb.set_trace()
                        # Make sure there is a record
                        if self.swath_record[self.swath_side].save_last():
                            # Build the message with outer points
                            outer_points = self.swath_record[self.swath_side].get_swath_outer_pts( \
                                self.swath_side)
                            self.outer_message = ''
                            for pt in outer_points:
                                self.outer_message += 'x=' + str(pt[0]) + ',y=' + str(pt[1]) + ';'
                            self.outer_message = self.outer_message[:-1]

                            # Build the message with swath widths
                            swath_widths = self.swath_record[self.swath_side].get_all_swath_widths()
                            width_message = [str(width) + ';' for width in swath_widths]
                            self.swath_record_message = ''.join(width_message)
                            self.swath_record_message = self.swath_record_message[:-1]

                            # Build full coverage model
                            try:
                                new_coverage = self.swath_record['stbd'].get_swath_coverage('stbd')
                                new_coverage = new_coverage.union(self.swath_record['port'].get_swath_coverage('port'))
                                self.coverage = self.coverage.union(new_coverage)
                            except Exception, e:
                                print("Error adding coverage")

                            self.swath_record['stbd'].reset_line()
                            self.swath_record['port'].reset_line()

                            self.post_ready = True
                        else:
                            print('Error: There is no swath record to post')
                    if msg.is_name('NEW_PATH'):
                        print('Eliminating Points In Existing Coverage')
                        next_path_pts = self.messages['NEW_PATH'].split(':')
                        if len(next_path_pts) > 0:
                            # for pt in next_path_pts:
                            #     next_path
                            next_path = [(float(pt.split(',')[0]), float(pt.split(',')[1])) \
                                for pt in next_path_pts]
                            new_len = len(next_path)
                            if REMOVE_IN_COVERAGE:
                                #if self.coverage.area != 0:
                                prepared_coverage = prep(self.coverage)
                                next_path = [pt for pt in next_path if not prepared_coverage.contains(Point(pt))]
                                print('Removed {0} points'.format(new_len - len(next_path)))

                            if len(next_path) < 3:
                                self.post_end = True
                                print('Path too short, ending survey')
                            else:
                                # this is actually the reverse of the start heading
                                start_heading = (next_path[0][0] - next_path[1][0], \
                                    next_path[0][1] - next_path[1][1])
                                start_heading = pathplan.unit_vector(start_heading)
                                self.start_line_message = 'points=' + \
                                        str(next_path[0][0] + start_heading[0] * ALIGNMENT_LINE_LEN) + ',' \
                                        + str(next_path[0][1] + start_heading[1] * ALIGNMENT_LINE_LEN) + \
                                        ':' + str(next_path[0][0]) + ',' + str(next_path[0][1])

                                point_list = [str(pt[0]) + ',' + str(pt[1]) + ':' for pt in next_path]
                                points_message = ''.join(point_list)
                                self.path_message = 'points=' + points_message[:-1]
                                self.path_ready = True
                        else:
                            print('No path points received')
            return True
        except Exception, e:
            print str(e)
            raise e
        return False

    def run(self):
        while True:
            time.sleep(0.1)
            if self.post_end:
                self.comms.notify('FAULT', 'true', pymoos.time())
                self.post_end = False
            if self.post_ready:
                print('Posting Swath edge to MOOSDB')
                self.comms.notify('SWATH_EDGE', self.outer_message, pymoos.time())
                self.comms.notify('SWATH_WIDTH_RECORD', self.swath_record_message, \
                    pymoos.time())
                self.comms.notify('NEXT_SWATH_SIDE', self.swath_side, pymoos.time())
                self.post_ready = False
            if self.path_ready:
                print('Posting Survey and Start line updates to MOOSDB')
                self.comms.notify('SURVEY_UPDATE', self.path_message, pymoos.time())
                self.comms.notify('START_UPDATE', self.start_line_message, pymoos.time())
                self.path_ready = False


def main():
    this_record = RecordSwath()
    this_record.run()
        
if __name__ == "__main__":
    main()
