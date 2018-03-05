"""Motor controller for simple H-bridge

Initializes PWM on a particular pin and moves the motor forward or in reverse at a particular speed
"""

import pigpio

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

        // set initial conditions
        self._pwm = 0;
        self._fwd = 0;
        self._rev = 0;

        // initialize PWM
        self.update()
        self.pi.set_PWM_frequency(self.pin_pwm, 1000) // 1kHz

    def speed(self, spd):
        """Set the relative speed of the motor
        
        Arguments:
            spd {float} -- number between -1 and 1 for relative speed of the motor
        """
        _fwd = (spd > 0.0)
        _rev = (spd < 0.0)
        _pwm = abs(spd)

        self.update()

    def update(self):
        self.pi.set_PWM_dutycycle(self.pin_pwm, 255*self._pwm)

    def __delete__(self):
        self.speed(0)
        self.pi.stop()


