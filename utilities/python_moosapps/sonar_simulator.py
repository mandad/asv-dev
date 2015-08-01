import pymoos
import time
# import gridgen


class SonarSimulator(object):
    def __init__(self):
        self.comms = pymoos.comms()
        self.comms.set_on_connect_callback(self.connect_callback)
        self.comms.set_on_mail_callback(self.message_received)
        self.comms.run('localhost', 9000, 'uSonarSimulator')
        # self.Simulator = 

        # Initialize stored variables
        self.messages = dict()
        self.messages['NAV_X'] = 0
        self.messages['NAV_Y'] = 0
        self.messages['NAV_HEADING'] = 0

    def connect_callback(self):
        result = True
        result = result and self.comms.register('NAV_X', 0)
        result = result and self.comms.register('NAV_Y', 0)
        result = result and self.comms.register('NAV_HEADING', 0)

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
                if msg.is_name('NAV_HEADING'):
                    print 'Posting swath width'
                    # Message in the format "port=52;stbd=37"
                    self.post_ready = True
                    self.post_message = 'port=15;stbd=20'
        except Exception, e:
            print 'Error'
            raise e

        return True

    def get_post_message(self, reset=True):
        if reset:
            self.post_ready = False
        return self.post_message

    def run(self):
        while True:
            time.sleep(1)
            if self.post_ready:
                print 'Notifying MOOSDB with swath width'
                self.comms.notify('SWATH_WIDTH', self.get_post_message(), \
                    pymoos.time())


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
