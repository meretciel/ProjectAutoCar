import autocar.interface as interface


class DistanceRadar(interface.Radar):
    def __init__(self,name=None,controller=None):
        self._name = name
        self._controller = controller
        self._raw_data = None



    @property
    def controller(self):
        return self._controller

    @property
    def raw_data(self):
        return self._raw_data




