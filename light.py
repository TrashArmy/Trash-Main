"""Class to control light

Initialize the NeoPixel light and turn it on or off with any color of your
choosing. See the 'main' portion for a simple example.
"""

import sys
sys.path.insert(0, './rpi_ws281x/python/')
from neopixel import *
import time

# NeoPixel configuration:
LED_COUNT      = 64      # Number of LED pixels.
# LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53
LED_STRIP      = ws.WS2811_STRIP_GRB   # Strip type and colour ordering


class Light:
    def __init__(self, pin_led):
        LED_PIN = pin_led
        # Create and configure NeoPixel object
        self.light_handle = Adafruit_NeoPixel(
            LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT,
            LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)
        # Intialize the library
        self.light_handle.begin()

        # Store the number of pixels
        self._num_pixels = self.light_handle.numPixels()

        # Set default color
        self._color = Color(127, 150, 127)

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        """Setter for color property

        Decorators:
            color.setter

        Arguments:
            color {[list]} -- list of color in [R, G, B] format, where R, G,
                              and B can range from 0 to 255
        """

        try:
            self._color = Color(color[0], color[1], color[2])
        except (IndexError):
            self._color = Color(255, 255, 255)

    def on(self):
        for i in range(self._num_pixels):
            self.light_handle.setPixelColor(i, self._color)
            self.light_handle.show()

    def off(self):
        for i in range(self._num_pixels):
            self.light_handle.setPixelColor(i, Color(0, 0, 0))
            self.light_handle.show()


if __name__ == '__main__':
    lh = Light(18)
    print('Lighting NeoPixel...')
    lh.on()
    time.sleep(10)
    print('Turning off NeoPixel...')
    lh.off()
