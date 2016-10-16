import time
import multiprocessing as mp

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

#        self._reference_pulse_left = left_wheel_comp.reference_pulse
#        self._reference_pulse_right = right_wheel_comp.reference_pulse
#        self._pulse_left = left_wheel_comp.pulse
#        self._pulse_right = right_wheel_comp.pulse

        self._cmd_Q_left = mp.Queue()
        self._cmd_Q_right = mp.Queue()
        self._output_Q_left = mp.Queue()
        self._output_Q_right = mp.Queue()

        self._left_wheel = ContinuousComponentWrapper(component=self._left_wheel_comp, cmd_Q=self._cmd_Q_left,output_Q=self._output_Q_left)
        self._right_wheel = ContinuousComponentWrapper(component=self._right_wheel_comp, cmd_Q=self._cmd_Q_right,output_Q=self._output_Q_right)


    def _change_speed(self, left_scale=0., right_scale=0.):
        """
        change the speed of the two wheels. A utility function.
        """
        self._cmd_Q_left.put(('increase_speed',(left_scale,), {}))
        self._cmd_Q_right.put(('increase_speed', (right_scale,), {}))


    def stop(self):
        """
        Breaks the robot. Set the wheels to be still.
        """
        self._cmd_Q_left.put(('stop', (), {}))
        self._cmd_Q_right.put(('stop', (), {}))

    def turn_left(self, scale=0.5, period=1.):
        """
        Turn left. The if scale = 0, the turn is slow; if the scale = 1., the turn is sharp.
        """
        scale = min(scale, 1)
        scale = max(scale, 0)
        left_scale = -(1 - scale)
        right_scale = scale
        self._change_speed(left_scale, right_scale)
        time.sleep(period)
        self.stop()
        self.increase_speed(self._startup_scale)


    def turn_right(self, scale=0.5, period=1.):
        """
        Turn right. The if scale = 0, the turn is slow; if the scale = 1., the turn is sharp.
        """
        scale = min(scale, 1)
        scale = max(scale, 0)

        left_scale = scale
        right_scale = -(1 - scale)

        self._change_speed(left_scale, right_scale)
        self.stop()
        self.increase_speed(self._startup_scale)
                



    def start(self):
        """
        Start the engine. This function will start the two wheels. 

        Note:
            The wheels are wrapped in the ContinuousComponentWrapper and they are multiprocessing.Process.
        """

        self._left_wheel.start()
        self._right_wheel.start()

        
