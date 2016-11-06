
import RPi.GPIO as gpio
import time

import numpy as np 

gpio.setmode(gpio.BOARD)

class WheelMotor:
    # default setting
    REFERENCE_PULSE     = 0.0014454
    MAX_PULSE_DEVIATION = 0.00025
    WIDTH               = 0.020
    def __init__(self, pin_signal=None, reference_pulse=None, max_pulse_deviation=None, width=None):
        assert pin_signal is not None
        self._pin_signal = pin_signal

        # if use does not specify the configuration of the motor, the default setting is used.
        self._reference_pulse = reference_pulse if reference_pulse is not None else WheelMotor.REFERENCE_PULSE
        self._max_pulse_deviation = max_pulse_deviation if max_pulse_deviation is not None else WheelMotor.MAX_PULSE_DEVIATION
        self._width = width if width is not None else WheelMotor.WIDTH


        gpio.setup(self._pin_signal, gpio.OUT, initial=0)

    def generate_pulse(self, repeat=10, pulse=None, width=None):
        if pulse is None:
            pulse = WheelMotor.reference_pulse
        if width is None:
            width = WheelMotor.width

        assert pulse <= self.reference_pulse + self.max_pulse_deviation

        pin = self._pin_signal
        gpio.output(pin,0)
        for n in range(repeat):
            gpio.output(pin,1)
            time.sleep(pulse)
            gpio.output(pin,0)
            time.sleep(width)

    @property
    def reference_pulse(self):
        return self._reference_pulse

    @property
    def max_pulse_deviation(self):
        return self._max_pulse_deviation

    @property
    def width(self):
        return self._width

if __name__ == '__main__':
    pin_signal = 13

    for pulse in np.arange(0.0013, 0.0016, 0.0001):
        print('pulse: {}'.format(pulse))
        generate_pulse(pin_signal,repeat=200,pulse=pulse,width=0.020)

