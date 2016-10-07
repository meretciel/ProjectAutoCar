import time
from abc import ABCMeta, abstractmethod
import multiprocessing as mp


from stepper_motor import StepperMotor
from distance_sensor import DistanceSensor


class Component(metaclass=ABCMeta):
    #TODO: add lock to component to make it safer
    @abstractmethod
    def send_msg(self,Q):
        """
        Send the message to the Q. Q should support put operation.
        Note that message is not incluced in the parameter list, it is the 
        responsibility of class to implement the process.
        """
        pass

    @abstractmethod
    def run(self):
        """
        Upon calling this function, the component will perform its routine work.
        """
        pass

    def parse_and_execute(self, msg_tuple):
        """
        This function will parse the arguments and call the member function accordingly.
        The msg_tuple should be (func_name, args, kwargs):
            func_name : the name fo the member function that will be called
            args      : the argument list. It is also a tuple.
            kwargs    : keyword argumetns. It is a dictionary

        """

        func_name, args, kwargs = msg_tuple
        func = getattr(self, func_name)
        func(*args, **kwargs)

    def update(self, attr, val):
        setattr(self, attr, val)

    def d_update(self, attr, val):
        orig_val = getattr(self,attr)
        setattr(self, attr, orig_val + val)


class DistanceRadarBaseComponent(Component):
    CLOCKWISE = 0
    ANTI_CLOCKWISE = 1
    def __init__(self, name=None, pins=None, initial_pos=0, degree=180, pre_rot=90,delay=0.002, step_size=5):
        assert name is not None

        self._stepper_motor = StepperMotor(pins,initial_pos)
        self._name = name
        self._degree = degree
        self._pre_rot = pre_rot
        self._delay = delay
        self._step_size = step_size
        
        self._zero_pos = None
        self._direction = self.ANTI_CLOCKWISE

        super(DistanceRadarBaseComponent, self).__init__()
        
    def initialize(self):
        if self._pre_rot < 0:
            self._stepper_motor.rotate(degree=-self._pre_rot, clockwise=False, delay=self._delay)
        elif self._pre_rot > 0:
            self._stepper_motor.rotate(degree=self._pre_rot, clockwise=True, delay=self._delay)

        # the current position is used as internal zero degree position
        # and this value shoulbe not be changed later
        self._zero_pos = self._stepper_motor.pos



    def run(self):

        if self._direction == self.ANTI_CLOCKWISE:
            self._stepper_motor.rotate(degree=self._step_size, clockwise=False, delay=self._delay)
            if self._stepper_motor.pos - self._zero_pos >= self._degree:
                self._direction = self.CLOCKWISE

        else:
            self._stepper_motor.rotate(degree=self._step_size, clockwise=True, delay=self._delay)
            if self._stepper_motor.pos - self._zero_pos <= 0:
                self._direction = self.ANTI_CLOCKWISE


    def send_msg(self,Q):
        msg = (time.time(), 'DistanceRadarBase::{}'.format(self._name), self._stepper_motor.pos, self.degree)
        Q.put(msg)

    
    @property
    def delay(self):
        return self._delay
    @delay.setter
    def delay(self,val):
        self._delay = val


    @property
    def degree(self):
        return self._degree
    @degree.setter
    def degree(self,val):
        self._degree = val
        
    @property
    def step_size(self):
        return self._step_size
    @step_size.setter
    def step_size(self, val):
        self._step_size = val




class DistanceRadarSensorComponent(Component):
    def __init__(self, name=None, pin_echo=None, pin_trig=None, unit='m'):
        assert name is not None

        self._name = name
        self._sensor = DistanceSensor(pin_echo=pin_echo, pin_trig=pin_trig, unit=unit)

        super(DistanceRadarSensorComponent,self).__init__()

    def run(self):
        self._sensor.measure(depay=self._delay)

    def send_msg(self,Q):
        msg = (time.time(), 'DistanceRadarSensor-{}'.format(self._name), self._sensor.distance)




class ContinuousComponentWrapper(mp.Process):
    """
    The ContinuousComponentWrapper is use to make a component running in the background.
    

    Args of __init__:
        component: an instance of component class.
        cmd_Q:     command queue. It is used to send command to the component when it is running in the background.
        output_Q:  output queue. The wrapper sends out message or informaiton through this queue.


    """
    def __init__(self, component=None, cmd_Q=None,output_Q=None):
        assert isinstance(component, Component)
        assert isinstance(cmd_Q, mp.queues.Queue)
        assert isinstance(output_Q, mp.queues.Queue)

        self._component = component
        self._output_Q = output_Q
        self._cmd_Q = cmd_Q
        super(ContinuousComponentWrapper,self).__init__()

    def loop(self, *args, **kwargs):
        """
        This function will allow the wrapper to run continuously by recusive call. At the begin of the loop, the internal
        event will wait. This is useful when other processes want to change the attributes of the component
        """
        #self._event.wait()
        while not self._cmd_Q.empty():
            cmd = self._cmd_Q.get()
            self._component.parse_and_execute(cmd)

        self._component.run()
        self._component.send_msg(self._output_Q)
        self.loop()

    def run(self):
        self.loop()


    @property
    def component(self):
        return self._component





if __name__ == '__main__':
    in_1 = 3
    in_2 = 5
    in_3 = 7
    in_4 = 11

    pins = [in_1, in_2, in_3, in_4 ]

    radar_base = DistanceRadarBaseComponent(
            name='radar_base', pins=pins, initial_pos=0, degree=180, pre_rot=0,delay=0.002
    )
    radar_base.initialize()
    cmd_Q = mp.Queue()
    output_Q = mp.Queue()

    cComponent = ContinuousComponentWrapper(component=radar_base, cmd_Q=cmd_Q,output_Q=output_Q)
    cComponent.start()


    for i in range(10):
        print('i:'.format(i))
        while not output_Q.empty():
            print(output_Q.get())
        time.sleep(3)
        cmd_Q.put(('update', ('degree', 180 - 5 * i), {}))




