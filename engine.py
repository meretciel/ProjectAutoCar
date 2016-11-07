import time
import multiprocessing as mp
import random

from components import WheelComponent, ContinuousComponentWrapper


class Engine:
    """
    Engine class controls the movement of the robot. It consists of two wheels.
    """

    def __init__(self, startup_scale=0.1, stable_scale=0.6, cmd_Q=None, output_Q=None,left_wheel_comp=None, right_wheel_comp=None):
        """
        Args:
            startup_scale:    float. It controls the start up sclae of the two wheel. 
            stable_scale:     float. It controls the speed of the wheel in the stable status.
            left_wheel_comp:  Instance of WheelComponent.
            right_wheel_comp: Instance of WheelComponent.
            cmd_Q: Do we need this?
            output_Q: Do we need this?

        Note:
            The function will construct the ContinuousComponentWrapper internally. The user of the class will not be able to control the two wheels
            directly. All the operations are performed through the Engine class.
        """
#        assert isinstance(cmd_Q, mp.queues.Queue)
#        assert isinstance(output_Q, mp.queues.Queue)

        assert isinstance(left_wheel_comp, WheelComponent)
        assert isinstance(right_wheel_comp, WheelComponent)

        self._cmd_Q = cmd_Q
        self._output_Q = output_Q
        self._left_wheel_comp = left_wheel_comp
        self._right_wheel_comp = right_wheel_comp

        self._startup_scale = startup_scale
        self._stacle_scale = stable_scale


        self._cmd_Q_left = mp.Queue()
        self._cmd_Q_right = mp.Queue()
        self._output_Q_left = mp.Queue()
        self._output_Q_right = mp.Queue()

        self._left_wheel  = ContinuousComponentWrapper(component=self._left_wheel_comp,  cmd_Q=self._cmd_Q_left, output_Q=self._output_Q_left)
        self._right_wheel = ContinuousComponentWrapper(component=self._right_wheel_comp, cmd_Q=self._cmd_Q_right,output_Q=self._output_Q_right)

        # infomration of wheel components
        self._left_pulse             = self._left_wheel.pulse
        self._right_pulse            = self._right_wheel.pulse
        self._left_reference_pulse   = self._left_wheel.reference_pulse
        self._right_reference_pulse  = self._right_wheel.reference_pulse
        self._left_max_deviation     = self._left_wheel.max_pulse_deviation
        self._right_max_deviation    = self._right_wheel.max_pulse_deviation
        self._left_mirro             = self._left_wheel.mirror
        self._right_mirro            = self._right_wheel.mirror

    
    def update_motor_stats(self):
        while not self._output_Q_left.empty():
            msg = self._output_Q_left.get(block=False)
            self._left_pulse = msg[2]

        while not self._output_Q_right.empty():
            msg = self._output_Q_right.get(block=False)
            self._right_pulse = msg[2]



    def _change_speed(self, left_scale=0., right_scale=0.):
        """
        change the speed of the two wheels. A utility function.
        """
        rdn_num = random.random()
        if rdn_num <= 0.5:
            self._cmd_Q_left.put(('increase_speed',  (left_scale,), {}))
            self._cmd_Q_right.put(('increase_speed', (right_scale,), {}))
        else:
            self._cmd_Q_right.put(('increase_speed', (right_scale,), {}))
            self._cmd_Q_left.put(('increase_speed',  (left_scale,), {}))

        self.update_motor_stats()


    def increase_speed(self, scale):
        self._change_speed(left_scale=scale, right_scale=scale)


    def stop(self):
        """
        Breaks the robot. Set the wheels to be still.
        """
        self._cmd_Q_left.put(('stop', (), {}))
        self._cmd_Q_right.put(('stop', (), {}))

    def go_straight(self):
        left_scale = abs(self._left_pulse - self._left_reference_pulse) / self._left_max_deviation
        right_scale = abs(self._right_pulse - self._right_reference_pulse) / self._right_max_deviation
        new_scale = 0.5 * (left_scale + right_scale)

        if self._left_pulse < self._left_reference_pulse:
            new_left_scale = -new_scale
        else:
            new_left_scale = new_scale


        if self._right_pulse < self._right_reference_pulse:
            new_right_scale = -new_scale
        else:
            new_right_scale = new_scale


        self._cmd_Q_left.put(('set_speed',(new_scale,), {}))
        self._cmd_Q_right.put(('set_speed', (new_scale,), {}))
        self.update_motor_stats()




    def turn_left(self, scale=0.5, weight=0.2, period=0.3):
        """
        Turn left. The if scale = 0, the turn is slow; if the scale = 1., the turn is sharp.
        """

        zero_left  = 0.
        zero_right = 0.
        one_left   = -0.5
        one_right  = 1.

        left_scale  = scale * (one_left  * weight + zero_left  * (1 - weight))
        right_scale = scale * (one_right * weight + zero_right * (1 - weight)) 


        self._change_speed(left_scale, right_scale)


    def turn_right(self, scale=0.5, weight=0.2, period=0.3):
        """
        Turn right. The if scale = 0, the turn is slow; if the scale = 1., the turn is sharp.
        """
        zero_left  = 0.
        zero_right = 0.
        one_left   = 1.
        one_right  = -0.5        

        left_scale  = scale * (one_left  * weight + zero_left  * (1 - weight))
        right_scale = scale * (one_right * weight + zero_right * (1 - weight)) 

        self._change_speed(left_scale, right_scale)

                



    def start(self):
        """
        Start the engine. This function will start the two wheels. 

        Note:
            The wheels are wrapped in the ContinuousComponentWrapper and they are multiprocessing.Process.
        """

        self._left_wheel.start()
        self._right_wheel.start()

        
