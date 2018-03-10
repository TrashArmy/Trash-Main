"""Servo controller for HS-805BB servos

Initializes PWM on a particular pin and sets the angle of the servo
"""

import pigpio
import time

class Servo_HS805BB:
    def __init__(self, pi, pin_pwm):
        self.pi = pi

        if not self.pi.connected:
           exit()

        self.pin_pwm = pin_pwm

        # servo characteristics
        self._center = 1500 # center pulsewidth
        self._width = 400 # pulsewidth from center to angle
        self._angle = 45 # angle 
        self._max_angle = 90
        self._min_angle = -90

        # set servo to center
        self._pulsewidth = self._center
        self.degree(0)

    @property
    def degree(self):
        return pw_to_d(self._pulsewidth)

    @degree.setter
    def degree(self, angle):
        self._pulsewidth = d_to_pw(angle)
        self.pi.set_servo_pulsewidth(self.pin_pwm, self._pulsewidth)

    def d_to_pw(self, angle):
        if angle > self._max_angle:
            angle = self._max_angle # set angle to max value
        elif angle < self._min_angle:
            angle = self._min_angle # set angle to min value

        pulsewidth = self._center + (angle*(self._width/self._angle))
        return pulsewidth

    def pw_to_d(self, pulsewidth):
        angle = ((pulsewidth-self._center)/self._width)*self._angle
        return angle

    def __delete__(self):
        self.pi.set_servo_pulsewidth(self.pin_pwm, 0) # turn off servo


if __name__ == '__main__':
    pi = pigpio.pi()

    s = Servo_HS805BB(18)
    s.degree(45)
    time.sleep(2)
    s.degree(90)
    time.sleep(2)
    s.degree(-90)
    time.sleep(4)
    s.degree(-45)
    time.sleep(2)
    s.degree(0)
    time.sleep(4)

    pi.stop()