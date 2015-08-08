import pymoos
import time
import pathplan
import pdb
# import gridgen

SWATH_OVERLAP = 0.2

class PathPlan(object):
    def __init__(self):
        self.comms = pymoos.comms()
        self.comms.set_on_connect_callback(self.connect_callback)
        self.comms.set_on_mail_callback(self.message_received)
        self.comms.run('localhost', 9000, 'pPathPlan')

        # Initialize stored variables
        self.messages = dict()
        self.messages['SWATH_EDGE'] = ''
        self.messages['SWATH_WIDTH_RECORD'] = ''
        self.messages['NEXT_SWATH_SIDE'] = 'stbd'
        self.messages['TURN_REACHED'] = 'false'
        self.post_ready = False
        self.post_message = ''
        self.turn_pt_message = ''
        self.start_line_message = ''
        self.need_to_process = False
        self.post_next_turn = False
        self.post_end = False
        # self.op_poly = [(16,-45), (50,-150), \
        #     (-85, -195), (-122, -70)]
        self.op_poly = [(4075.0, -650.0), (3293, -2464), (2405, -2259), \
            (3180, -387)]

        # VIEW_SEGLIST = "pts={10,-26:16,-45},label=emily_waypt_line_start,
        # label_color=white,edge_color=white,vertex_color=dodger_blue,
        # vertex_size=3,edge_size=1"

        pts_list = [str(pt[0]) + ',' + str(pt[1]) + ':' for pt in self.op_poly]
        # Back to the beginning
        pts_list.append(str(self.op_poly[0][0]) + ',' + str(self.op_poly[0][1]))
        pts_string = ''.join(pts_list)
        region_message = 'pts={' + pts_string + '},label=op_region,' + \
        'label_color=red,edge_color=red,vertex_color=red,edge_size=2'

        # Make sure we can send the message
        if self.comms.wait_until_connected(2000):
            print 'Posting op region: ' + pts_string
            self.comms.notify('VIEW_SEGLIST', region_message, pymoos.time())
        else:
            print 'Timed out connecting before sending op region'

    def connect_callback(self):
        result = True
        result = result and self.comms.register('SWATH_EDGE', 0)
        result = result and self.comms.register('NEXT_SWATH_SIDE', 0)
        result = result and self.comms.register('SWATH_WIDTH_RECORD', 0)
        result = result and self.comms.register('TURN_REACHED', 0)

        return result

    def message_received(self):
        try:
            for msg in self.comms.fetch():
                # Shouldn't ever be binary message
                print 'Checking message type and getting message'
                if msg.is_double():
                    self.messages[msg.name()] = msg.double()
                else:
                    self.messages[msg.name()] = msg.string()

                # Arbitrary message triggers output
                if msg.is_name('NEXT_SWATH_SIDE'):
                    self.need_to_process = True
                if msg.is_name('TURN_REACHED'):
                    self.post_next_turn = True;

                if self.need_to_process and (len(self.messages['SWATH_WIDTH_RECORD']) > 0):
                    self.need_to_process = False
                    
                    print 'Initiating path planning'
                    # process MOOS message points into list
                    if len(self.messages['SWATH_EDGE']) > 0:
                        print 'Getting edge points'
                        edge_pts = self.messages['SWATH_EDGE'].split(';')
                        outer_rec = []
                        for pt in edge_pts:
                            xy = pt.split(',')
                            if len(xy) > 1:
                                x = xy[0].split('=')
                                y = xy[1].split('=')
                                outer_rec.append((float(x[1]), float(y[1])))
                        # pdb.set_trace()
                        if len(self.messages['SWATH_WIDTH_RECORD']) > 0:
                            print 'Getting Swath Widths'
                            swath_widths = self.messages['SWATH_WIDTH_RECORD'].split(';')
                            swath_widths = [float(sw) for sw in swath_widths]

                            if len(swath_widths) != len(outer_rec):
                                print 'Different number of swath widths and locations, aborting'
                                return False

                            print 'Planning next path'
                            path_planner = pathplan.PathPlan(None, \
                                self.messages['NEXT_SWATH_SIDE'], SWATH_OVERLAP, \
                                outer_rec, swath_widths)
                            # This is where to add an opregion if needed
                            next_pts = path_planner.generate_next_path(self.op_poly)

                            if len(next_pts) > 1:
                                point_list = [str(pt[0]) + ',' + str(pt[1]) + ':' for pt in next_pts]
                                points_message = ''.join(point_list)

                                # Message in the format "points=x1,y1:x2,y2 ..."
                                # self.post_message = 'points=' + points_message[:-1]
                                self.post_message = points_message[:-1]

                                end_heading = (next_pts[-1][0] - next_pts[-2][0], \
                                    next_pts[-1][1] - next_pts[-2][1])
                                # this is actually the reverse of the start heading
                                start_heading = (next_pts[0][0] - next_pts[1][0], \
                                    next_pts[0][1] - next_pts[1][1])
                                end_heading = pathplan.unit_vector(end_heading)
                                start_heading = pathplan.unit_vector(start_heading)

                                self.turn_pt_message = 'point=' + \
                                    str(next_pts[-1][0] + end_heading[0] * 30) + ',' \
                                    + str(next_pts[-1][1] + end_heading[1] * 30)
                                self.start_line_message = 'points=' + \
                                    str(next_pts[0][0] + start_heading[0] * 20) + ',' \
                                    + str(next_pts[0][1] + start_heading[1] * 20) + \
                                    ':' + str(next_pts[0][0]) + ',' + str(next_pts[0][1])

                                self.post_ready = True
                            else:
                                self.post_ready = False
                                self.post_end = True
                else:
                    self.post_ready = False
        except Exception, e:
            print 'Error:' + str(e)
            raise e

        return True

    def get_post_message(self, reset=True):
        if reset:
            self.post_ready = False
        return self.post_message

    def run(self):
        while True:
            time.sleep(0.5)
            if self.post_ready:
                print 'Notifying MOOSDB with new path'
                self.comms.notify('NEW_PATH', self.get_post_message(), \
                    pymoos.time())
                self.comms.notify('START_UPDATE', self.start_line_message, pymoos.time())
            if self.post_next_turn:
                self.comms.notify('TURN_UPDATE', self.turn_pt_message, pymoos.time())
                self.post_next_turn = False
            if self.post_end:
                self.comms.notify('FAULT', 'true', pymoos.time())
                self.post_end = False




def main():
    this_path_plan = PathPlan()
    this_path_plan.run()

        
if __name__ == "__main__":
    main()
