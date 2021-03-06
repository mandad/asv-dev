import pymoos
import time
import pathplan
import pdb
# import gridgen

SWATH_OVERLAP = 0.2
# For actually running Z-Boat
TURN_PT_OFFSET = 15
ALIGNMENT_LINE_LEN = 10

# Sim
#TURN_PT_OFFSET = 50
#ALIGNMENT_LINE_LEN = 30

class PathPlan(object):
    def __init__(self):
        self.comms = pymoos.comms()
        self.comms.set_on_connect_callback(self.connect_callback)
        self.comms.set_on_mail_callback(self.message_received)
        pymoos.set_moos_timewarp($(WARP))
        self.comms.set_comms_control_timewarp_scale_factor(0.4)
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
        self.turn_count = 0
        # self.op_poly = [(16,-45), (50,-150), \
        #     (-85, -195), (-122, -70)]
        # SH 15 North Survey area:
        # self.op_poly = [(4075.0, -650.0), (3293, -2464), (2405, -2259), \
        #     (3180, -387)]
        # SH15 South Survey Area:
        # self.op_poly = [(2497.0, -4374.0), (1727, -6077), (588, -5468), \
             # (1272, -3864)]
        # Small region for half step testing, SH 2015
        # self.op_poly = [(655, -4429), (550, -4813), (198, -4725), (300, -4353)]
        self.op_poly = $(OP_POLY)
        
        # Newport, RI
        #self.op_poly = [ (-229,47), (-279,217), (-41,264), (0,100)]
    	# South of Pier
        #self.op_poly = [ (-167, -194), (-136, -342), (199, -255), (142, -107) ]
    	# Smaller South of Pier
    	# self.op_poly = [ (-210, -192), (-191,-307), (10,-254), (-16,-144)]

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
            print('Updating lines')
            # Put these in a function
            point_list = [str(pt[0]) + ',' + str(pt[1]) + ':' for pt in self.op_poly[0:2]]
            points_message = ''.join(point_list)
            points_message = 'points=' + points_message[:-1]
            self.comms.notify('SURVEY_UPDATE', points_message, pymoos.time())

            start_heading = (self.op_poly[0][0] - self.op_poly[1][0], \
                self.op_poly[0][1] - self.op_poly[1][1])
            start_heading = pathplan.unit_vector(start_heading)
            start_line_message = 'points=' + \
                str(self.op_poly[0][0] + start_heading[0] * ALIGNMENT_LINE_LEN) + ',' \
                + str(self.op_poly[0][1] + start_heading[1] * ALIGNMENT_LINE_LEN) + \
                ':' + str(self.op_poly[0][0]) + ',' + str(self.op_poly[0][1])
            self.comms.notify('START_UPDATE', start_line_message, pymoos.time())

            end_heading = (self.op_poly[1][0] - self.op_poly[0][0], \
                self.op_poly[1][1] - self.op_poly[0][1])
            end_heading = pathplan.unit_vector(end_heading)
            turn_pt_message = 'point=' + \
                str(self.op_poly[1][0] + end_heading[0] * TURN_PT_OFFSET) + ',' \
                + str(self.op_poly[1][1] + end_heading[1] * TURN_PT_OFFSET)
            self.comms.notify('TURN_UPDATE', turn_pt_message, pymoos.time())

            home_message = 'station_pt = ' + str(self.op_poly[0][0] + \
                start_heading[0] * 30) + ',' + str(self.op_poly[0][1] + \
                start_heading[1] * 30)
            self.comms.notify('HOME_UPDATE', home_message, pymoos.time())


            # move boat to start
            # self.comms.notify('NAV_X', str(self.op_poly[0][0] + \
            #     start_heading[0] * 30), pymoos.time())
            # self.comms.notify('NAV_Y', str(self.op_poly[0][1] + \
            #     start_heading[1] * 30), pymoos.time())

            # pdb.set_trace()

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
                    self.turn_count += 1
                    self.post_next_turn = True;

                if self.need_to_process and (len(self.messages['SWATH_WIDTH_RECORD']) > 0):
                    
                    print '\n**** Initiating path planning ****'
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
                            self.need_to_process = False
                            print 'Getting Swath Widths'
                            swath_widths = self.messages['SWATH_WIDTH_RECORD'].split(';')
                            swath_widths = [float(sw) for sw in swath_widths]

                            # All swath widths are zero when they have been filtered by depth
                            if all(width == 0 for width in swath_widths):
                                print 'Depth threshold reached, ending.'
                                self.post_end = True
                            else:
                                if len(swath_widths) != len(outer_rec):
                                    print 'Different number of swath widths and locations, aborting'
                                    return False

                                print 'Planning next path'
                                path_planner = pathplan.PathPlan(None, \
                                    self.messages['NEXT_SWATH_SIDE'], SWATH_OVERLAP, \
                                    outer_rec, swath_widths)
                                # This is where to add an opregion if needed
                                next_pts = path_planner.generate_next_path(self.op_poly)

                                print('Number of pts in new_path: {0}'.format(len(next_pts)))

                                if len(next_pts) > 1:
                                    point_list = [str(pt[0]) + ',' + str(pt[1]) + ':' for pt in next_pts]
                                    points_message = ''.join(point_list)

                                    # Message in the format "points=x1,y1:x2,y2 ..."
                                    # self.post_message = 'points=' + points_message[:-1]
                                    self.post_message = points_message[:-1]

                                    end_heading = (next_pts[-1][0] - next_pts[-2][0], \
                                        next_pts[-1][1] - next_pts[-2][1])
                                    end_heading = pathplan.unit_vector(end_heading)
                                    self.turn_pt_message = 'point=' + \
                                        str(next_pts[-1][0] + end_heading[0] * TURN_PT_OFFSET) + ',' \
                                        + str(next_pts[-1][1] + end_heading[1] * TURN_PT_OFFSET)
                                    self.turn_count = 0

                                    print('Setting post_ready=True')
                                    self.post_ready = True
                                else:
                                    self.post_ready = False
                                    self.post_end = True
                else:
                    pass
                    # self.post_ready = False
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
            time.sleep(0.1)
            if self.post_ready:
                print 'Notifying MOOSDB with new path\n'
                self.comms.notify('NEW_PATH', self.get_post_message(), \
                    pymoos.time())
                
            if self.post_next_turn and self.turn_count == 1:
                print 'Posting turn update'
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
