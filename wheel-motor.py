
import RPi.GPIO as gpio
import time

import numpy as np 

gpio.setmode(gpio.BOARD)

signal_pin = 13


gpio.setup(signal_pin, gpio.OUT, initial=0)



def generate_pulse(pin, repeat=1000, pulse=0.00145, width=0.020):
    assert pulse <= width
    gpio.output(pin,0)
    for n in range(repeat):
        gpio.output(pin,1)
        time.sleep(pulse)
        gpio.output(pin,0)
        time.sleep(width)


if __name__ == '__main__':
#    print("test default setting. The default setting should be still")
#    generate_pulse(signal_pin)
    for pulse in np.arange(0.0013, 0.0016, 0.0001):
        print('pulse: {}'.format(pulse))
        generate_pulse(signal_pin,repeat=200,pulse=pulse,width=0.020)

