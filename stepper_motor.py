
import RPi.GPIO as gpio
import time
import math

gpio.setmode(gpio.BOARD)


class StepperMotor:
    """
    StepperMotor is a class the represents a stepper motor. It provides functions to control the motor and keeps record of
    the motor status.

    Attributes:
        pins:      Pins used to send signal to stepper motor. pins is a list of length 4 because the a common stepper motor has 4 inputs.
        init_pos:  Double. It represents the position of the motore. It is set by the user and is quite arbitrary.
        delta_pos: Double. The cumulative change of the position.
    """

    def __init__(self, pins, init_pos=0):
        assert isinstance(pins, list) and len(pins) == 4, 'Invalid pins.'

        self._pins = list(pins)
        for pin in self._pins:
            gpio.setup(pin, gpio.OUT, initial=0)

        time.sleep(1.0)

        self._init_pos = init_pos 
        self._delta_pos = 0.
        super(StepperMotor, self).__init__()

    def rotate(self, degree=None, clockwise=False, delay=0.002):
        """
        Calling the rorate function will make the motor rotate. The degree controls the range of the movement. If the degree is None, the
        motor will not stop. The dealy controls the speed of the motor. 
        """
        if clockwise:
            in_1, in_2, in_3, in_4 = self._pins[::-1]
        else:
            in_1, in_2, in_3, in_4 = self._pins

        if degree is None:
            remaining = 1
        else:
            remaining = degree

        #TODO: remove the hard-coded number
        stepsize = 360. / 4096.  * 8

        while degree is None or remaining > 0:
            gpio.output(in_1, 1); time.sleep(delay); 
            gpio.output(in_4, 0); time.sleep(delay); 
            gpio.output(in_2, 1); time.sleep(delay); 
            gpio.output(in_1, 0); time.sleep(delay); 
            gpio.output(in_3, 1); time.sleep(delay); 
            gpio.output(in_2, 0); time.sleep(delay); 
            gpio.output(in_4, 1); time.sleep(delay); 
            gpio.output(in_3, 0); time.sleep(delay); 

            if degree is not None:
                remaining -= stepsize

            if clockwise:
                self._delta_pos -= stepsize
            else:
                self._delta_pos += stepsize
            
    def turn_off_all_pins(self):
        for pin in self._pins:
            gpio.output(pin,0)

    def scan(self, degree=180, pre_rot=90, delay=0.002):
        """
        Upon calling the scan function, the motor will make a round-trip. We can also specify a pre-scan movenent to
        adjust the initial position of the motor.

        Args:
            degree:  The max degree the will be covered by the scan. 360 represetn a full scan cricle.
            pre_rot: The specifies the movenent of the motor before it enters the loop. The positive degree 
                     means the motor will spin anti-clockwisely; the negative degree meansthe motor will spin clockwisely.
            delay:   This parameter controls the speed of the scan.

        """

        # pre-rotate and the motor will be back to the zero position
        if pre_rot < 0:
            self.rotate(degree=-pre_rot, clockwise=True, delay=delay)
        elif pre_rot > 0:
            self.rotate(degree=pre_rot, clockwise=False, delay=delay)

        self.rotate(degree=degree, clockwise=False,delay=delay)
        self.turn_off_all_pins()
        time.sleep(3 * delay)

        self.rotate(degree=degree, clockwise=True,delay=delay)
        self.turn_off_all_pins()
        time.sleep(3 * delay)


    @property
    def delta_pos(self):
        return self._delta_pos

    @property
    def pos(self):
        return self._init_pos + self.delta_pos


if __name__ == '__main__':

    in_1 = 3
    in_2 = 5
    in_3 = 7
    in_4 = 11

    pins = [in_1, in_2, in_3, in_4 ]
    stepperMotor = StepperMotor(pins)

    time.sleep(2.)
    print('call stepperMotor.rotate()')
    input('press any key to start')
#    stepperMotor.rotate()
    stepperMotor.scan(pre_rot=90)
    #swing(pins, degree=180)
    



