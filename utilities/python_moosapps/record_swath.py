import pymoos
import time
import followpath
import pathplan
import pdb

SWATH_INTERVAL = 10 #meters
NEXT_PATH_SIDE = ['port', 'stbd']

class RecordSwath(object):
    def __init__(self):
        self.comms = pymoos.comms()
        self.comms.set_on_connect_callback(self.connect_callback)
        self.comms.set_on_mail_callback(self.message_received)
        self.comms.run('localhost', 9000, 'uRecordSwath')
        self.swath_record = dict()
        self.swath_record['port'] = followpath.RecordSwath(SWATH_INTERVAL)
        self.swath_record['stbd'] = followpath.RecordSwath(SWATH_INTERVAL)

        # Initialize stored variables
        self.messages = dict()
        self.messages['SWATH_WIDTH'] = 0
        self.messages['NAV_X'] = 0
        self.messages['NAV_Y'] = 0
        self.messages['NAV_HEADING'] = 0
        self.messages['LINE_END'] = 0
        self.messages['LINE_BEGIN'] = 0
        self.messages['NEXT_SWATH_SIDE'] = 'port'
        self.swath_side = 'port'
        self.next_swath_side = 0
        self.post_ready = False
        self.recording = False  # this gets set when the line starts

    def connect_callback(self):
        result = True
        result = result and self.comms.register('SWATH_WIDTH', 0)
        result = result and self.comms.register('NAV_X', 0)
        result = result and self.comms.register('NAV_Y', 0)
        result = result and self.comms.register('NAV_HEADING', 0)
        result = result and self.comms.register('LINE_END', 0)
        result = result and self.comms.register('LINE_BEGIN', 0)
        result = result and self.comms.register('NEXT_SWATH_SIDE', 0)

        return result

    def message_received(self):
        try:
            for msg in self.comms.fetch():
                # Shouldn't ever be binary message
                if msg.is_double():
                    self.messages[msg.name()] = msg.double()
                else:
                    self.messages[msg.name()] = msg.string()

                if msg.is_name('SWATH_WIDTH') and self.recording:
                    # Message in the format "port=52;stbd=37"
                    for split_msg in self.messages['SWATH_WIDTH'].split(';'):
                        print "Received Swath Width {0}".format(split_msg)
                        widths = split_msg.split('=')
                        self.swath_record[widths[0]].record(float(widths[1]), \
                            self.messages['NAV_X'], self.messages['NAV_Y'], \
                            self.messages['NAV_HEADING'])

                if msg.is_name('LINE_BEGIN'):
                    print "Line beginning, starting to record swath"
                    self.recording = True

                if msg.is_name('LINE_END'):
                    self.recording = False
                    # Publish swath generation side, and trigger pPathPlan
                    self.next_swath_side += 1
                    self.swath_side = NEXT_PATH_SIDE[self.next_swath_side % 2]
                    print 'End of Line, outputting swath points on ' + self.swath_side + ' side.'

                    # Record the last point
                    # pdb.set_trace()
                    # self.swath_record[self.swath_side].min_interval()
                    self.swath_record[self.swath_side].save_last()
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

                    self.swath_record['stbd'].reset_line()
                    self.swath_record['port'].reset_line()

                    self.post_ready = True
            return True
        except Exception, e:
            print str(e)
            raise e
        return False

    def run(self):
        while True:
            time.sleep(1)
            if self.post_ready:
                self.comms.notify('SWATH_EDGE', self.outer_message, pymoos.time())
                self.comms.notify('SWATH_WIDTH_RECORD', self.swath_record_message, \
                    pymoos.time())
                self.comms.notify('NEXT_SWATH_SIDE', \
                    self.swath_side, pymoos.time())
                self.post_ready = False


def main():
    this_record = RecordSwath()
    this_record.run()
        
if __name__ == "__main__":
    main()
