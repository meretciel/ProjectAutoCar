
import RPi.GPIO as gpio
import time

gpio.setmode(gpio.BOARD)


in_1 = 3
in_2 = 5
in_3 = 7
in_4 = 11


# set all motor input to 0
gpio.setup(in_1, gpio.OUT, initial=0)
gpio.setup(in_2, gpio.OUT, initial=0)
gpio.setup(in_3, gpio.OUT, initial=0)
gpio.setup(in_4, gpio.OUT, initial=0)


time.sleep(1.5)

tt = 0.002


def rotate(pins, degree=None, clockwise=False, delay=0.002):
    if clockwise:
        in_1, in_2, in_3, in_4 = pins[::-1]
    else:
        in_1, in_2, in_3, in_4 = pins

    if degree is None:
        remaining = 1
    else:
        remaining = degree
    
    print(in_1,in_2,in_3,in_4)

    stepsize = 360. / 4096.  * 8
    while degree is None or remaining > 0:
        print('remaining: {}'.format(remaining))
        gpio.output(in_1, 1); time.sleep(delay); 
        gpio.output(in_4, 0); time.sleep(delay); 
        gpio.output(in_2, 1); time.sleep(delay); 
        gpio.output(in_1, 0); time.sleep(delay); 
        gpio.output(in_3, 1); time.sleep(delay); 
        gpio.output(in_2, 0); time.sleep(delay); 
        gpio.output(in_4, 1); time.sleep(delay); 
        gpio.output(in_3, 0); time.sleep(delay); 
        remaining -= stepsize

def swing(pins, degree=180, delay=0.002):
    while True:
        rotate(pins, degree=degree, clockwise=True,delay=delay)
        for pin in pins:
            gpio.output(pin,0)
        time.sleep(3 * delay)
        rotate(pins, degree=degree, clockwise=False,delay=delay)
        for pin in pins:
            gpio.output(pin,0)
        time.sleep(3 * delay)

if __name__ == '__main__':
    print("starat")
    time.sleep(2)
    pins = [in_1, in_2, in_3, in_4 ]
    #rotate([in_1, in_2, in_3, in_4], degree=360)
    swing(pins, degree=180)
    



