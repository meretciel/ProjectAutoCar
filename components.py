import time
from abc import ABCMeta, abstractmethod
import multiprocessing as mp


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

    def parse(self, msg_tuple):
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




class MyComponent(Component):
    def __init__(self, x):
        self._x = x

    def send_msg(self, Q):
        Q.put(str(self._x) + str(time.time()))

    def run(self):
        print("MyComponent::{}".format(self._x))
        time.sleep(0.5)

    def parse(self, msg_tuple):
        func_name, args, kwargs = msg_tuple
        func = getattr(self, func_name)
        func(*args, **kwargs)

    def increase_speed(self,delta):
        self._x += delta




class ComponentWrapper(mp.Process):
    def __init__(self, component=None, event=None, cmd_Q=None,output=None):
        self._component = component
        self._output = output_Q
        self._cmd_Q = cmd_Q
        self._event = event

        # set event to be true so the wrapepr can
        # run from the beginning.
        self._event.set()
        super(ComponentWrapper,self).__init__()

    def loop(self, *args, **kwargs):
        """
        This function will allow the wrapper to run continuously by recusive call. At the begin of the loop, the internal
        event will wait. This is useful when other processes want to change the attributes of the component
        """
        #self._event.wait()
        while not self._cmd_Q.empty():
            cmd = self._cmd_Q.get()
            self._component.parse(cmd)

        self._component.run()
        self._component.send_msg(self._output)
        self.loop()

    def run(self):
        self.loop()


    @property
    def component(self):
        return self._component





if __name__ == '__main__':
    myComponent = MyComponent(10)
    myEvent = mp.Event()
    output_Q = mp.Queue()
    cmd_Q = mp.Queue()

    wrapper = ComponentWrapper(component=myComponent, cmd_Q=cmd_Q, event=myEvent,output=output_Q)
    wrapper.start()


    for t in range(10):
        myEvent.clear()
        cmd_Q.put(('increase_speed', (t,), {}))
        while not output_Q.empty():
            print(output_Q.get())
        myEvent.set()
        time.sleep(1.5)




    wrapper.join()




