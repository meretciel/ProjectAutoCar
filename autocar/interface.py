from abc import abstractmethod, abstractproperty



class Radar:

    @abstractmethod
    def send_signal(self, *args, **kwargs):
        pass

    @abstractmethod
    def recv_signal(self, *args, **kwargs):
        pass

    @abstractmethod
    def process(self, *args, **kwargs):
        pass


    def detect(self,*args, **kwargs):
        self.send_signal(*args, **kwargs)
        self.recv_signal(*args, **kwargs)
        self.process(*args, **kwargs)


    def send_raw_data(self, raw_data, controller):
        controller.recv_raw_data(raw_data)



class Controller:

    @abstractmethod
    def recv_raw_data(self, raw_data):
        pass


    def send_command(self, command, invoker):
        invoker.recv(command)


class Invoker:
    @abstractmethod
    def execute(self,command):
        pass

    @abstractmethod
    def recv(self,command):
        pass 