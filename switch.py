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

        self._prevprev = 0
        self._prev = 0
        self._curr = 0

    def read(self):
        tmp = pi.read(self.pin_switch)

        # Only update value if read value is different from old current value
        if (self._curr != tmp):
            self._prevprev = self._prev
            self._prev = self._curr
            self._curr = tmp

        return self._curr

    def toggled(self):
        self.read()
        if (self._prevprev == self._curr and self._prevprev != self.prev):
            if (self._curr == 0):
                # Reset to prevent multiple toggles
                self._prevprev = self._prev

                return 1
            elif (self._curr == 1):
                # Reset to prevent multiple toggles
                self._prevprev = self._prev

                return 2
            else:
                return False
        else:
            return False

if __name__ == '__main__':
    pi = pigpio.pi()

    s = Switch(pi, 26)
    try:
        while(True):
            print(s.read())
            print(s.toggled())
            time.sleep(0.1)  # 100 ms
    except (KeyboardInterrupt):
        pi.stop()
