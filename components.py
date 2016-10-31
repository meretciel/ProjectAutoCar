import time
from abc import ABCMeta, abstractmethod
import multiprocessing as mp


from stepper_motor import StepperMotor
from distance_sensor import DistanceSensor
from controller import RawDataHandler
from wheel_motor import WheelMotor

CMD_EXIT = '__exit__'

class Component(metaclass=ABCMeta):


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

        #TODO: add exit status

        len_tuple = len(msg_tuple)

        if len_tuple == 1:
            func_name = msg_tuple[0]
            args = ()
            kwargs = {}
        elif len_tuple == 2:
            func_name = msg_tuple[0]
            comp = msg_tuple[1]
            args = ()
            kwargs = {}
            if isinstance(comp, tuple):
                args = comp
            elif isinstance(comp, dict):
                kwargs = comp



        else: # all components are present
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


    def __getattr__(self, attr):
        return getattr(self.component, attr)


    def run(self):
        """
        Running the component in the infinite loop. To change the status of the component, one can send command to the command queue.
        #TODO: add a stop-pill
        """
        try:

            while True:
                while not self._cmd_Q.empty():
                    cmd = self._cmd_Q.get()
                    if cmd == CMD_EXIT or cmd == (CMD_EXIT,):
                        return 
                    self._component.parse_and_execute(cmd)


                self._component.run()
                self._component.send_msg(self._output_Q)

        except KeyboardInterrupt:
            if hasattr(self._component, 'KeyboardInterruptHandler'):
                self._component.KeyboardInterruptHandler()
            print('{} property exit after KeyboardInterrupt.'.format(self._component.name))



    @property
    def component(self):
        return self._component


    @property
    def cmd_Q(self):
        return self._cmd_Q

    @property
    def output_Q(self):
        return self._output_Q





class DistanceRadarBaseComponent(Component):
    CLOCKWISE = 0
    ANTI_CLOCKWISE = 1
    FORMAT = ('timestamp', 'comp_name', 'pos', 'min_degree', 'max_degree')
    def __init__(self, name=None, pins=None, initial_pos=0, min_degree=0, max_degree=180, delay=0.002, delay_factor=3, step_size=5):
        assert name is not None

        self._stepper_motor = StepperMotor(pins,initial_pos)
        self._name = name
        self._init_pos = initial_pos
        self._min_degree = min_degree
        self._max_degree = max_degree
        self._delay = delay
        self._delay_factor = delay_factor
        self._step_size = step_size
        
        self._direction = self.ANTI_CLOCKWISE


        super(DistanceRadarBaseComponent, self).__init__()
        
    def initialize(self):

        if self._init_pos < self._min_degree or self._init_pos > self._max_degree:
            new_init_pos = (self._min_degree + self._max_degree) / 2
            if new_init_pos > self._init_pos:
                self._stepper_motor.rotate(degree=new_init_pos - self._init_pos, clockwise=False, delay=self._delay)
            else:
                self._stepper_motor.rotate(degree=self._init_pos - new_init_pos, clockwise=True, delay=self._delay)



    def run(self):

        if self._direction == self.ANTI_CLOCKWISE:
            self._stepper_motor.rotate(degree=self._step_size, clockwise=False, delay=self._delay)
            if self._stepper_motor.pos > self._max_degree :
                self._direction = self.CLOCKWISE
                time.sleep(self._delay * self._delay_factor)

        else:
            self._stepper_motor.rotate(degree=self._step_size, clockwise=True, delay=self._delay)
            if self._stepper_motor.pos < self._min_degree:
                self._direction = self.ANTI_CLOCKWISE
                time.sleep(self._delay * self._delay_factor)


    def send_msg(self,Q):
        msg = (time.time(), 'DistanceRadarBase::{}'.format(self._name), self._stepper_motor.pos, self.min_degree, self.max_degree)
        Q.put(msg)

    def KeyboardInterruptHandler(self):
        self._stepper_motor.back_to_zero_pos(delay=self._delay)

    
    @property
    def delay(self):
        return self._delay
    @delay.setter
    def delay(self,val):
        self._delay = val


#    @property
#    def degree(self):
#        return self._degree
#    @degree.setter
#    def degree(self,val):
#        self._degree = val
    
    @property
    def max_degree(self):
        return self._max_degree

    @property
    def min_degree(self):
        return self._min_degree
        
    @property
    def step_size(self):
        return self._step_size
    @step_size.setter
    def step_size(self, val):
        self._step_size = val




class DistanceRadarSensorComponent(Component):
    FORMAT = ('timestamp','comp_name','distance','status')
    def __init__(self, name=None, pin_echo=None, pin_trig=None, unit='m', delay=0.00001):
        assert name is not None

        self._name = name
        self._sensor = DistanceSensor(pin_echo=pin_echo, pin_trig=pin_trig, unit=unit)
        self._measure_result = (None,DistanceSensor.INIT)
        self._delay = delay


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
    FORMAT = ('timestamp', 'comp_name', 'pulse', 'repeat')

    def __init__(self, name=None, mirror=False, pin_signal=None, repeat=10, pulse=None, width=None):
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
                            of the slient period. If the width is None, it will be set to the width value of the underlaying motor class.

        """

        assert name is not None
        assert pin_signal is not None
        self._name = name
        self._pin_signal = pin_signal
        self._motor = WheelMotor(pin_signal=self._pin_signal)
        self._reference_pulse = self._motor.reference_pulse
        self._max_deviation = self._motor.max_pulse_deviation
        self._max_pulse = self._reference_pulse + self._max_deviation
        self._min_pulse = self._reference_pulse - self._max_deviation

        self._pulse = pulse if pulse is not None else self._reference_pulse
        self._width = width if width is not None else self._motor.width
        self._repeat = repeat
        self._mirror = mirror


    def run(self):
        self._motor.generate_pulse(repeat=self._repeat,pulse=self._pulse, width=0.020)

    def send_msg(self,Q):
        Q.put((time.time(), 'WheelComponent::{}'.format(self._name), self.pulse, self.repeat))

    @property
    def pulse(self):
        return self._pulse
    @pulse.setter
    def pulse(self, val):
        self._pulse = min(val, self._width)

    @property
    def reference_pulse(self):
        return self._reference_pulse

    @property
    def repeat(self):
        return self._repeat
    @repeat.setter
    def repeat(self,val):
        self._repeat = min(val, 50)

    def increase_speed(self, scale, block=False):
        """
        increase the speed of the wheel motor. 
        
        Args:
            scale: float. The valid/effective range of scale is -2 to 2 depending on the status of the wheel motor. If the value is outside this range,
                          There will be no warning. In order to increase the speed of the motor, we will chagne the value of pulse. Each motor has a 
                          reference pulse which makes the motor still and a max deviation of the pulse. When we increase the speed by scale, the effect
                          is increase the current pulse by max_deviation_of_pulse * scale. If the new pulse will be adjusted to be inside the max
                          deviation.
            block: bool. Default is True. When block is set True, the increase_speed function cannot change the direction of the rotation. 

        """
#        scale = min(scale, 1.)
#        scale = max(scale, -1.)

        increment = scale *  self._max_deviation

        if self._mirror:
            increment = -1 * increment

        curr_pulse = self.pulse
        new_pulse = curr_pulse + increment

        if block:
                
            if curr_pulse >= self._reference_pulse:
                new_pulse = min(self._max_pulse, new_pulse)
                new_pulse = max(self._reference_pulse, new_pulse)
            else:
                new_pulse = min(self._reference_pulse, new_pulse)
                new_pulse = max(self._min_pulse, new_pulse)

        else:
            new_pulse = min(self._max_pulse, new_pulse)
            new_pulse = max(self._min_pulse, new_pulse)


        self._pulse = new_pulse

    def stop(self):
        self._pulse = self._reference_pulse






        







if __name__ == '__main__':
#
    # set up the radar base
    in_1 = 3
    in_2 = 5
    in_3 = 7
    in_4 = 11

    pins = [in_1, in_2, in_3, in_4 ]

    radar_base = DistanceRadarBaseComponent(name='radar_base', pins=pins, step_size=0.71, initial_pos=0, min_degree=-60, max_degree=40, delay=0.0025)
    radar_base.initialize()
    radar_base_param = RawDataHandler(name=radar_base.name, parser=radar_base.FORMAT, record_size=2000)

    cmd_Q_base    = mp.Queue()
    output_Q_base = mp.Queue()

    cont_radar_base = ContinuousComponentWrapper(component=radar_base, cmd_Q=cmd_Q_base, output_Q=output_Q_base)


    # set up the distance sensor
    pin_echo = 18
    pin_trig = 16

    cmd_Q_sensor = mp.Queue()
    output_Q_sensor = mp.Queue()

    distance_sensor = DistanceRadarSensorComponent(name='radar_distance_sensor', pin_echo=pin_echo, pin_trig=pin_trig, delay=0.00007)
    distance_sensor_param = RawDataHandler(name=distance_sensor.name, parser=distance_sensor.FORMAT, record_size=2000)

    cont_distance_sensor = ContinuousComponentWrapper(component=distance_sensor, cmd_Q=cmd_Q_sensor, output_Q=output_Q_sensor)

    print("start the processin 3s")
    time.sleep(3)

    cont_radar_base.start()
    cont_distance_sensor.start()

    _start =time.time()
    try:
        while True:
    #        while not output_Q_sensor.empty():
    #            msg = output_Q_sensor.get()
    #            print(msg)
    #            distance_sensor_param.update(msg)

            while not output_Q_base.empty():
                msg = output_Q_base.get()
                print(msg)
                radar_base_param.update(msg)

            if time.time() - _start > 90:
                break
    except KeyboardInterrupt:
        cmd_Q_base.put(CMD_EXIT)
        print("properly exit")
        
        pass
    
#    distance_sensor_param.data.to_csv('sensor_data.csv')
#    radar_base_param.data.to_csv('radar_base.csv')

    

#    pin_signal_left = 13
#    pin_signal_right = 15
#
#    left_wheel_component  = WheelComponent(name='left_wheel', mirror=False, pin_signal=pin_signal_left, repeat=20, pulse=None, width=None)
#    right_wheel_component = WheelComponent(name='right_wheel', mirror=True, pin_signal=pin_signal_right, repeat=20, pulse=None, width=None)
#
#    cmd_Q_left_wheel = mp.Queue()
#    output_Q_left_wheel = mp.Queue()
#    cmd_Q_right_wheel = mp.Queue()
#    output_Q_right_wheel = mp.Queue()
#
#
#    left_wheel = ContinuousComponentWrapper(component=left_wheel_component,cmd_Q=cmd_Q_left_wheel,output_Q=output_Q_left_wheel)
#    right_wheel = ContinuousComponentWrapper(component=right_wheel_component,cmd_Q=cmd_Q_right_wheel,output_Q=output_Q_right_wheel)
#
#
#    left_wheel.start()
#    right_wheel.start()
#
#    scale = 0.
#    while True:
#        print('scale: {}'.format(scale))
#        time.sleep(3)
#        cmd_Q_left_wheel.put(('increase_speed',(0.05,), {}))
#        cmd_Q_right_wheel.put(('increase_speed', (0.05,), {}))
#        scale += 0.1
#


    









