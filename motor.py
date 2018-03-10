"""Motor controller for simple H-bridge

Initializes PWM on a particular pin and moves the motor forward or in reverse at a particular speed
"""

import pigpio
import time

class Motor:
    def __init__(self, pin_pwm, pin_fwd, pin_rev):
        """Initialize the motor controller
        
        Arguments:
            pin_pwm {int} -- GPIO pin connected to PWM control
            pin_fwd {int} -- GPIO pin connected to FWD control
            pin_rev {int} -- GPIO pin connected to REV control
        """
        self.pi = pigpio.pi()

        if not self.pi.connected:
           exit()

        self.pin_pwm = pin_pwm
        self.pin_fwd = pin_fwd
        self.pin_rev = pin_rev

        # set initial conditions
        self._pwm = 0;
        self._fwd = 0;
        self._rev = 0;

        # initialize fwd/rev/pwm pins and update
        self.pi.set_mode(self.pin_fwd, pigpio.OUTPUT)
        self.pi.set_mode(self.pin_rev, pigpio.OUTPUT)
        self.pi.set_PWM_frequency(self.pin_pwm, 1000) // 1kHz
        self.update()

    def speed(self, spd):
        """Set the relative speed of the motor
        
        Arguments:
            spd {float} -- number between -1 and 1 for relative speed of the motor
        """
        if abs(spd) > 1:
            spd = 0
            
        self._fwd = (spd > 0.0)
        self._rev = (spd < 0.0)
        self._pwm = abs(spd)

        if self.update():
            return True
        else:
            return False

    def update(self):
        self.pi.set_PWM_dutycycle(self.pin_pwm, 255*self._pwm)
        self.pi.write(self.pin_fwd, self._fwd)
        self.pi.write(self.pin_rev, self._rev)

        if self.pi.read(self.pin_fwd) == self._fwd and self.pi.read(self.pin_rev) == self._rev:
            return True
        else:
            return False

    def __delete__(self):
        self.speed(0)
        self.pi.stop()

if __name__ == '__main__':
    m = Motor(18, 24, 25)
    m.speed(1)
    time.sleep(5)
    m.speed(-1)
    time.sleep(5)
    m.speed(0)
    time.sleep(5)
    m.speed(1)
    time.sleep(5)
    m.speed(-0.5)
    time.sleep(10)
