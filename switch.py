"""Switch controller
"""

import pigpio
import time

class Switch:
    def __init__(self, pi, pin_switch):
        self.pi = pi

        if not self.pi.connected:
           exit()

        self.pin_switch = pin_switch
        pi.set_mode(self.pin_switch, pigpio.INPUT)
        pi.set_pull_up_down(self.pin_switch, pigpio.PUD_DOWN)

    def read(self):
        return pi.read(self.pin_switch)


if __name__ == '__main__':
    pi = pigpio.pi()

    s = Switch(pi, 26)
    try:
        while(True):
            print(s.read())
    except (KeyboardInterrupt):
        pi.stop()
            

    pi.stop()

