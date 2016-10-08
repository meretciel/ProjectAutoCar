import pandas as pd 
class Status:
    def __init__(self,*args, **kwargs):


        self._last = {}
        self._current = {}
        self._new = {}

        # initialize the parameter. The initial values are put under "last status"
        for item in args:
            if isinstance(item, tuple) and len(item) == 2:
                self._last[item[0]] = item[1]
            else:
                self._last[item] = None




    def update(self, attr, val):
        """
        Update the value of an attribute. The updated values are stored in "new" attribute.
        """
        self._new[attr] = val

    def compute_current_param(self):
        """
        Use information in "new" section and "last" section to compute the "current" status.
        User can define his own approach to estimate the current status.
        """
        pass

    def rotate(self):
        """
        Rotate function will rotate the status. More specifically, current becomes last.
        """
        self._last = self._current




    @property
    def last(self):
        return self._last

    @property
    def current(self):
        return self._current

    @property
    def new(self):
        return self._new



class RawDataHandler:
    def __init__(self, name=None, parser=None, record_size=100):
        assert name is not None and parser is not None
        self._name = name
        self._records     = []
        self._record_size = record_size
        self._parser = parser
        self._columns = [x[0] for x in self._parser]

    def update(self, msg):
        if len(self._records) == self._record_size:
            self._records.pop(0)

        # parse the msg
        record = []
        for attr, idx in self._parser:
            record.append(msg[idx])
        self._records.append(record)
    

    @property
    def data(self):
        df = pd.DataFrame(self._records, columns=self._columns)
        df['param_name'] = self._name
        return df




#class DistanceRadarSensorDataHandler(RawDataHandler):
#    PARSER = DistanceRadarSensorComponent.PARSER
#    pass
#
#
#class DistanceRadarBaseDataHandler(RawDataHandler):
#    PARSER = DistanceRadarBaseComponent.PARSER
#    pass
#


class Controller:
    pass 




