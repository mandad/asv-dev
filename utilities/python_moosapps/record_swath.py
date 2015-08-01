import pymoos
import time
import followpath
import pathplan

SWATH_INTERVAL = 10 #meters
NEXT_PATH_SIDE = ['port', 'stbd']
SWATH_OVERLAP = 0.2

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
        self.messages['NEXT_SWATH_SIDE'] = 'port'
        self.swath_side = 'port'
        self.next_swath_side = 0

    def connect_callback(self):
        result = True
        result = result and self.comms.register('SWATH_WIDTH', 0)
        result = result and self.comms.register('NAV_X', 0)
        result = result and self.comms.register('NAV_Y', 0)
        result = result and self.comms.register('NAV_HEADING', 0)
        result = result and self.comms.register('LINE_END', 0)
        result = result and self.comms.register('NEXT_SWATH_SIDE', 0)

        return result

    def message_received(self):
        for msg in self.comms.fetch():
            # Shouldn't ever be binary message
            if msg.is_double():
                self.messages[msg.name()] = msg.double()
            else:
                self.messages[msg.name()] = msg.string()

            if msg.is_name('SWATH_WIDTH'):
                # Message in the format "port=52;stbd=37"
                for split_msg in self.messages['SWATH_WIDTH'].split(';'):
                    widths = split_msg.split('=')
                    self.swath_record[widths[0]].record(widths[1], \
                        self.messages['NAV_X'], self.messages['NAV_Y'], \
                        self.messages['NAV_HEADING'])

            if msg.is_name('LINE_END'):
                print 'End of Line, outputting swath points'
                # path_planner = pathplan.PathPlan(self.swath_record[NEXT_PATH_SIDE[i % 2]], \
                        # NEXT_PATH_SIDE[i % 2], SWATH_OVERLAP)
                # next_path = path_planner.generate_next_path(self.op_poly)

                # Publish swath generation side, and trigger pPathPlan
                self.next_swath_side += 1
                self.swath_side = NEXT_PATH_SIDE[self.next_swath_side % 2]

                # Record the last point
                self.swath_record[self.swath_side].min_interval()
                outer_points = self.swath_record[self.swath_side].get_swath_outer_pts( \
                    self.swath_side)
                outer_message = ''
                for pt in outer_points:
                    outer_message += 'x=' + pt[0] + ',y=' + pt[1] + ';'
                comms.notify('SWATH_EDGE', outer_message, pymoos.time())
                comms.notify('NEXT_SWATH_SIDE', \
                    self.swath_side, pymoos.time())

        return True

def main():
    this_record = RecordSwath()
    while True:
        pass
        
if __name__ == "__main__":
    main()
