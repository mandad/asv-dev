import pymoos
import time
import gridgen
import followpath
import beamtrace

RAY_TRACE_RES = 1.0
SWATH_ANGLE = 70
PRINT_DEBUG = False
OUTPUT_MODE = "Depth"
DEPTH_THRESHOLD_HALFSTEP = 6
DEPTH_THRESHOLD_HALT = 5

class SonarSimulator(object):
    def __init__(self):
        self.bathy_grid = gridgen.BathyGrid.from_bathymetry( \
            $(BATHY_GRID), False)

        self.comms = pymoos.comms()
        self.comms.set_on_connect_callback(self.connect_callback)
        self.comms.set_on_mail_callback(self.message_received)
        pymoos.set_moos_timewarp($(WARP))
        self.comms.set_comms_control_timewarp_scale_factor(0.4)
        self.comms.run('localhost', 9000, 'uSonarSimulator')

        # Initialize stored variables
        self.messages = dict()
        self.messages['NAV_X'] = 0
        self.messages['NAV_Y'] = 0
        self.messages['NAV_HEADING'] = 0
        self.messages['NEXT_SWATH_SIDE'] = 'stbd'
        self.post_ready = False

        self.swath_angle = SWATH_ANGLE
        self.last_port_depth = 0
        self.last_stbd_depth = 0
        self.msg_count = 0

    def connect_callback(self):
        result = True
        result = result and self.comms.register('NAV_X', 0)
        result = result and self.comms.register('NAV_Y', 0)
        result = result and self.comms.register('NAV_HEADING', 0)
        result = result and self.comms.register('NEXT_SWATH_SIDE', 0)

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

                # Arbitrary message triggers output
                if msg.is_name('NAV_HEADING'):
                    # Allows skipping messages
                    self.msg_count += 1
                    if self.msg_count > 1:
                        self.msg_count = 0
                        if self.messages['NAV_X'] != 0 and self.messages['NAV_Y'] != 0:
                            print 'Posting swath width'
                            # Message in the format "port=52;stbd=37"
                            self.post_ready = True
                            current_loc = (self.messages['NAV_X'] + $(X_OFFSET), \
                                self.messages['NAV_Y'] + $(Y_OFFSET))
                            if OUTPUT_MODE == "Depth":
                                depths = self.get_depths(current_loc, \
                                    self.messages['NAV_HEADING'])
                                if self.messages['NEXT_SWATH_SIDE'] == 'port':
                                    side = 1
                                else:
                                    side = 0
                                swaths = [0, 0]
                                swaths[0] = beamtrace.width_from_depth(self.swath_angle, depths[0])
                                swaths[1] = beamtrace.width_from_depth(self.swath_angle, depths[1])
                                # Fudge in some half stepping
                                if depths[side] < DEPTH_THRESHOLD_HALT:
                                    print('Depth less than halt threshold: {0:.2f}'.format(depths[side]))
                                    swaths[side] = 0
                                elif depths[side] < DEPTH_THRESHOLD_HALFSTEP:
                                    print('Depth at half step threshold: {0:.2f}'.format(depths[side]))
                                    swaths[side] = swaths[side] / 2
                                self.post_message = 'x=' + str(self.messages['NAV_X']) + \
                                    ';y=' + str(self.messages['NAV_Y']) + ';hdg=' + \
                                    str(self.messages['NAV_HEADING']) + ';port=' +  \
                                    str(swaths[0])  +  ';stbd='  + str(swaths[1])

                            else:
                                swaths = self.get_swath_widths(current_loc, \
                                    self.messages['NAV_HEADING'])
                                self.post_message = 'x=' + str(self.messages['NAV_X']) + \
                                    ';y=' + str(self.messages['NAV_Y']) + ';hdg=' + \
                                    str(self.messages['NAV_HEADING']) + ';port=' +  \
                                    str(swaths[0])  +  ';stbd='  + str(swaths[1])
        except Exception, e:
            print 'Error: ' + str(e)
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
                print 'Notifying MOOSDB with swath width'
                # if OUTPUT_MODE == "Depth":
                #     self.comms.notify('SONAR_DEPTH_PORT_M', self.get_post_message(), pymoos.time())
                #     self.comms.notify('SONAR_DEPTH_STBD_M', self.get_post_message(), pymoos.time())
                # else:
                self.comms.notify('SWATH_WIDTH', self.get_post_message(), \
                    pymoos.time())

    def get_swath_widths(self, this_loc, hdg_deg):
        """
        Convert heading to vector, get perpendicular, ray trace it, then store this depth
        In normal operation, we would just get the heading and loc from vehicle and swath
        from the sonar
        """
        depths = self.get_depths(this_loc, hdg_deg)

        # Record port side swath
        swath_width = beamtrace.width_from_depth(self.swath_angle, depths[0])
        port_width = swath_width

        # Record stbd side swath
        swath_width = beamtrace.width_from_depth(self.swath_angle, depths[1])
        stbd_width = swath_width

        return (port_width, stbd_width)

    def get_depths(self, this_loc, hdg_deg):
        """Just get the depth from the swath instead of the width, so it can be passed to
        the sonar filter"""
        hdg_x, hdg_y = followpath.vector_from_heading(hdg_deg, 1)

        # Record port side swath
        beam_x, beam_y = beamtrace.hdg_to_beam(hdg_x, hdg_y, 'port')
        ray_trace = beamtrace.ray_depth(self.bathy_grid, self.swath_angle, \
            this_loc[0], this_loc[1], beam_x, beam_y, RAY_TRACE_RES, self.last_port_depth)
        self.last_port_depth = ray_trace[2]  # z-coord
        if PRINT_DEBUG:
            print('Port Depth: {0:.2f}\tSwath: {1:.2f}'.format(ray_trace[2], swath_width))

        # Record stbd side swath
        beam_x, beam_y = beamtrace.hdg_to_beam(hdg_x, hdg_y, 'stbd')
        ray_trace = beamtrace.ray_depth(self.bathy_grid, self.swath_angle, \
            this_loc[0], this_loc[1], beam_x, beam_y, RAY_TRACE_RES, self.last_stbd_depth)
        self.last_stbd_depth = ray_trace[2]
        if PRINT_DEBUG:
            print('Stbd Depth: {0:.2f}\tSwath: {1:.2f}'.format(ray_trace[2], swath_width))

        return (self.last_port_depth, self.last_stbd_depth)


def main():
    this_sonar_sim = SonarSimulator()
    this_sonar_sim.run()
    # while True:
    #     time.sleep(1)
    #     if this_sonar_sim.post_ready:
    #         print 'Notifying MOOSDB with swath width'
    #         this_sonar_sim.comms.notify('SWATH_WIDTH', this_sonar_sim.get_post_message(), \
    #             pymoos.time())

        
if __name__ == "__main__":
    main()
