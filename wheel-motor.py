
import RPi.GPIO as gpio
import time

import numpy as np 

gpio.setmode(gpio.BOARD)

class WheelMotor:
    reference_pulse     = 0.00145
    max_pulse_deviation = 0.00035
    def __inti__(self, pin_signal=None):
        assert signal_pin is not None
        self._signal_pin = pin_signal
        gpio.setup(self._signal_pin, gpio.OUT, initial=0)

    def generate_pulse(self, repeat=10, pulse=0.00145, width=0.020):
        assert pulse <= self.reference_pulse + self.max_pulse_deviation
        pin = self._signal_pin
        gpio.output(pin,0)
        for n in range(repeat):
            gpio.output(pin,1)
            time.sleep(pulse)
            gpio.output(pin,0)
            time.sleep(width)

if __name__ == '__main__':
    signal_pin = 13

    for pulse in np.arange(0.0013, 0.0016, 0.0001):
        print('pulse: {}'.format(pulse))
        generate_pulse(signal_pin,repeat=200,pulse=pulse,width=0.020)

