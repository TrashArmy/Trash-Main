#!/usr/bin/env python

import time
import pigpio

class Sonar:
   """
   This class encapsulates a type of acoustic ranger.  In particular
   the type of ranger with separate trigger and echo pins.

   A pulse on the trigger initiates the sonar ping and shortly
   afterwards a sonar pulse is transmitted and the echo pin
   goes high.  The echo pins stays high until a sonar echo is
   received (or the response times-out).  The time between
   the high and low edges indicates the sonar round trip time.
   """

   def __init__(self, pi, trigger, echo):
      """
      The class is instantiated with the Pi to use and the
      gpios connected to the trigger and echo pins.
      """
      self.pi    = pi
      self._trig = trigger
      self._echo = echo

      self._ping = False
      self._high = None
      self._time = None

      self._triggered = False

      self._trig_mode = pi.get_mode(self._trig)
      self._echo_mode = pi.get_mode(self._echo)

      pi.set_mode(self._trig, pigpio.OUTPUT)
      pi.set_mode(self._echo, pigpio.INPUT)

      self._cb = pi.callback(self._trig, pigpio.EITHER_EDGE, self._cbf)
      self._cb = pi.callback(self._echo, pigpio.EITHER_EDGE, self._cbf)

      self._inited = True

   def _cbf(self, gpio, level, tick):
      if gpio == self._trig:
         if level == 0: # trigger sent
            self._triggered = True
            self._high = None
      else:
         if self._triggered:
            if level == 1:
               self._high = tick
            else:
               if self._high is not None:
                  self._time = tick - self._high
                  self._high = None
                  self._ping = True

   def read(self):
      """
      Triggers a reading.  The returned reading is the number
      of microseconds for the sonar round-trip.

      round trip cms = round trip time / 1000000.0 * 34030
      """
      if self._inited:
         self._ping = False
         self.pi.gpio_trigger(self._trig)
         start = time.time()
         while not self._ping:
            if (time.time()-start) > 5.0:
               return 20000
            time.sleep(0.001)
         return self._time
      else:
         return None

   def read_cm(self):
      """
      Triggers a reading and converts to centimeters.
      """
      rtt = self.read()
      if rtt:
         return (rtt/1000000.0)*34030
      else:
         return None

   def read_cm_avg(self, num, dt = 0.03, min = 2, max = 400):
      """
      Takes num readings with time dt between readings and converts to centimeters.
      """
      rtt = 0
      vals = num
      for i in range(1, num):
         r = self.read_cm()
         if r > max or r < min:
            vals -= 1
         else:
            rtt += r

         time.sleep(dt)

      if vals < 1:
         return None

      rtt = rtt/vals
      return rtt
      #return (rtt/1000000.0)*34030


   def cancel(self):
      """
      Cancels the ranger and returns the gpios to their
      original mode.
      """
      if self._inited:
         self._inited = False
         self._cb.cancel()
         self.pi.set_mode(self._trig, self._trig_mode)
         self.pi.set_mode(self._echo, self._echo_mode)


if __name__ == "__main__":
   pi = pigpio.pi()

   s = Sonar(pi, 20, 21)
   while(True):
       print(s.read_cm())
       time.sleep(0.2)
   sonar.cancel()
   
   pi.stop()