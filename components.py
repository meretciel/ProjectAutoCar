import time
from abc import ABCMeta, abstractmethod
import multiprocessing as mp


from stepper_motor import StepperMotor
from distance_sensor import DistanceSensor
from controller import RawDataHandler
from wheel_motor.py import WheelMotor


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

    @property
    def name(self):
        return self._name

    @property
    def parser(self):
        return self._parser



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

    def run(self):
        """
        Running the component in the infinite loop. To change the status of the component, one can send command to the command queue.
        #TODO: add a stop-pill
        """
        while True:
            while not self._cmd_Q.empty():
                cmd = self._cmd_Q.get()
                self._component.parse_and_execute(cmd)

            self._component.run()
            self._component.send_msg(self._output_Q)



    @property
    def component(self):
        return self._component






class DistanceRadarBaseComponent(Component):
    CLOCKWISE = 0
    ANTI_CLOCKWISE = 1
    PARSER = [(x,i) for i, x in enumerate(['timestamp','comp_name','pos','degree'])]

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

        self._parser = DistanceRadarBaseComponent.PARSER

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
    PARSER = [(x,i) for i,x in enumerate(['timestamp','comp_name','distance', 'status'])]
    def __init__(self, name=None, pin_echo=None, pin_trig=None, unit='m', delay=0.00001):
        assert name is not None

        self._name = name
        self._sensor = DistanceSensor(pin_echo=pin_echo, pin_trig=pin_trig, unit=unit)
        self._measure_result = (None,DistanceSensor.INIT)
        self._delay = delay

        self._parser =  DistanceRadarSensorComponent.PARSER

        super(DistanceRadarSensorComponent,self).__init__()

    def run(self):
        self._measure_result = self._sensor.measure()
        time.sleep(self._delay)

    def send_msg(self,Q):
        res = self._measure_result
        msg = (time.time(), 'DistanceRadarSensor::{}'.format(self._name), res[0], res[1])
        Q.put(msg)



class WheelComponent(Component):
    """
    Represent a single wheel.
    """

    def __init__(self, name=None, mirror=False, pin_siganl=None, repeat=10, pulse=None, width=0.020):
        """
        Args:
            name:           the name of the component.
            mirror:         Bool. The left wheel and right wheel is a mirro image of each other. Therefore, with the same configuration and the 
                            same operaton the effect is opposite. For example, let assume we are in a scenario where when we increase the pulse, 
                            the motor spins faster clockwisely. If this motor is used for right wheel, when the pulse is increased, the robot will
                            be speed up; while if it is used for right wheel, the robot will be slowed down. This is a mirror effect. The mirror 
                            parameter is used to handle the mirror effet so we can have a unified interface to control both the left and right wheel.
            pin_signal:     the pin number for sending the pulse to the motor.
            pulse:          the pulse that is send to the motor. If the pulse is None,it will be set to the reference pulse of the underlying motor 
                            class, which make the motor still. The default value of pulse is None.
            repeat:         the number pulse sent to the motor in a cycle.
            width:          In the communication protocol, the signal consists of two parts: (1)pulse and (2)silence. The width specifies the length 
                            of the slient period.

        """

        assert name is not None
        assert pin_signal is not None
        self._name = name
        self._pin_signal = pin_signal
        self._motor = WheelMotor(pin_signal = self._pin_signal)
        self._reference_pulse = self._motor.reference_pulse
        self._max_deviation = self._motor.max_pulse_deviation
        self._max_pulse = self._reference_pulse + self._max_deviation
        self._min_pulse = self._reference_pulse - self._max_deviation

        self._pulse = pulse if pulse is not None else self._reference_pulse
        self._width = width
        self._repeat = repeat
        self._mirror = mirror


    def run(self):
        self._motor.generate_pulse(repeat=self._repeat,pulse=self._pulse, width=0.020)

    def send_msg(self,Q):
        pass

    @property
    def pulse(self):
        return self._pulse
    @pulse.setter
    def pulse(self, val):
        self._pulse = min(val, self._width)


    @property
    def repeat(self):
        return self._repeat
    @repeat.setter
    def repeat(self,val):
        self._repeat = min(val, 50)

    def increase_speed(self, scale):
        scale = min(scale, 1.)
        scale = max(scale, -1.)

        increment = scale *  self._max_deviation

        if self._mirror:
            increment = -1 * increment

        new_pulse = self.pulse + increment
        new_pulse = min(self._max_pulse, new_pulse)
        new_pulse = max(self._min_pulse, new_pulse)

        self._pulse = new_pulse






        







if __name__ == '__main__':

    # set up the radar base
    in_1 = 3
    in_2 = 5
    in_3 = 7
    in_4 = 11

    pins = [in_1, in_2, in_3, in_4 ]

    radar_base = DistanceRadarBaseComponent(name='radar_base', pins=pins, step_size=0.71, initial_pos=0, degree=80, pre_rot=40,delay=0.0025)
    radar_base.initialize()
    radar_base_param = RawDataHandler(name=radar_base.name, parser=radar_base.parser, record_size=2000)

    cmd_Q_base    = mp.Queue()
    output_Q_base = mp.Queue()

    cont_radar_base = ContinuousComponentWrapper(component=radar_base, cmd_Q=cmd_Q_base, output_Q=output_Q_base)


    # set up the distance sensor
    pin_echo = 18
    pin_trig = 16

    cmd_Q_sensor = mp.Queue()
    output_Q_sensor = mp.Queue()

    distance_sensor = DistanceRadarSensorComponent(name='radar_distance_sensor', pin_echo=pin_echo, pin_trig=pin_trig, delay=0.00007)
    distance_sensor_param = RawDataHandler(name=distance_sensor.name, parser=distance_sensor.parser, record_size=2000)

    cont_distance_sensor = ContinuousComponentWrapper(component=distance_sensor, cmd_Q=cmd_Q_sensor, output_Q=output_Q_sensor)

    print("start the processin 3s")
    time.sleep(3)

    cont_radar_base.start()
    cont_distance_sensor.start()

    _start =time.time()
    while True:
        while not output_Q_sensor.empty():
            msg = output_Q_sensor.get()
            print(msg)
            distance_sensor_param.update(msg)

        while not output_Q_base.empty():
            msg = output_Q_base.get()
            print(msg)
            radar_base_param.update(msg)

        if time.time() - _start > 90:
            break
    
    distance_sensor_param.data.to_csv('sensor_data.csv')
    radar_base_param.data.to_csv('radar_base.csv')

    # start the parallel process
#    cont_radar_base.join()
#    cont_distance_sensor.join()








