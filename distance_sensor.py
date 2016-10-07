
import RPi.GPIO as gpio
import time

#gpio.setmode(gpio.BCM)
gpio.setmode(gpio.BOARD)



class DistanceSensor:
    SUCC    = 'SUCC'
    INIT    = 'INIT'
    TIMEOUT = 'TIMEOUT'
    FAIL    = 'FAIL'

    def __init__(self, pin_echo=None, pin_trig=None, unit='m'):
        assert pin_echo is not None and pin_trig is not None
        self._pin_echo = pin_echo
        self._pin_trig = pin_trig

        gpio.setup(pin_echo, gpio.IN, pull_up_down=gpio.PUD_DOWN)
        gpio.setup(pin_trig, gpio.OUT, initial=0)
        time.sleep(1.)

        self._pulse = 0.00001
        self._status = DistanceSensor.INIT
        self._latest_measure = (None, DistanceSensor.INIT)

    def measure_once(self):
        """
        measure the distance once. The returnd value is (distance, status)
        """

        # send out the signal
        gpio.output(self._pin_trig, 1)
        time.sleep(self._pulse)
        gpio.output(self._pin_trig, 0)

        start = time.time()
        _start = start

        while gpio.input(self._pin_echo) == 0: # no echo signal received
            if time.time() - _start > 1.:
                self._status = DistanceSensor.TIMEOUT 
                break
            start = time.time()

        if self._status == DistanceSensor.TIMEOUT:
            return None, self._status

        while gpio.input(self._pin_echo) == 1: # receiving the echo signal
            stop = time.time()


        distance_m = 170. * (stop - start)

        # sanity check
        if distance_m < 0.04 or distance_m > 4:
            self._status = DistanceSensor.FAIL
            distance_m = None

        else:
            self._status = DistanceSensor.SUCC

        return distance_m, self._status

    def measure(self, delay=0.1):
        """
        Measure the distance several times. The Measure function will return a coroutine.
        """
        try:
            while True:
                msg = (yield)
                self._latest_measure = self.measure_once()
                time.sleep(delay)
        except GeneratorExit:
            print('disconnect to the distance sensor')
            pass


                    

if __name__ == '__main__':
    echo = 18
    trig = 16

    distance_sensor = DistanceSensor(pin_echo=echo, pin_trig=trig)

    input('press any key to start')

    #print(distance_sensor.measure_once())
    observer = distance_sensor.measure(repeat=30)
    next(observer)
    
    res = []

    for msg in ['m','m','m','stop']:
        observer.send(msg)
        res.append(distance_sensor._latest_measure)

    observer.close()

    for item in res:
        print(item)
                


