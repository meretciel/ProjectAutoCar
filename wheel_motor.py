
import RPi.GPIO as gpio
import time

import numpy as np 

gpio.setmode(gpio.BOARD)

class WheelMotor:
    reference_pulse     = 0.00145
    max_pulse_deviation = 0.00035
    width               = 0.020
    def __init__(self, pin_signal=None):
        assert pin_signal is not None
        self._pin_signal = pin_signal
        gpio.setup(self._pin_signal, gpio.OUT, initial=0)

    def generate_pulse(self, repeat=10, pulse=None, width=None):
        if pulse is None:
            pulse = WheelMotor.reference_pulse
        if width is None:
            width = WheelMotor.width

        assert pulse <= WheelMotor.reference_pulse + WheelMotor.max_pulse_deviation

        pin = self._pin_signal
        gpio.output(pin,0)
        for n in range(repeat):
            gpio.output(pin,1)
            time.sleep(pulse)
            gpio.output(pin,0)
            time.sleep(width)

if __name__ == '__main__':
    pin_signal = 13

    for pulse in np.arange(0.0013, 0.0016, 0.0001):
        print('pulse: {}'.format(pulse))
        generate_pulse(pin_signal,repeat=200,pulse=pulse,width=0.020)

