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
        self._columns = parser

    def update(self, msg):
        if len(self._records) == self._record_size:
            self._records.pop(0)

        # parse the msg
        self._records.append(list(msg))
    

    @property
    def data(self):
        df = pd.DataFrame(self._records, columns=self._columns)
        df['param_name'] = self._name
        return df


#class DistanceSensorDataHandler(RawDataHandler):
#    FORMAT=DistanceRadarSensorComponent.FORMAT
#    def __init__(self,name=None, record_size=500):
#        super(DistanceRadarSensorDataHandler, self).__init__(name=name, parser=DistanceSensorDataHandler.FORMAT,record_size=record_size)
#
#
#    @property
#    def 







#class DistanceRadarSensorDataHandler(RawDataHandler):
#    PARSER = DistanceRadarSensorComponent.PARSER
#    pass
#
#
#class DistanceRadarBaseDataHandler(RawDataHandler):
#    PARSER = DistanceRadarBaseComponent.PARSER
#    pass
#

T_FACTOR = 1e4

def format_timestamp(ts,factor=T_FACTOR):
    return (ts * factor).astype(int)

def create_distance_map(df_radar_base, df_distance_sensor):
    """
    Create the distance map. The map represents the environment in front of the robot. It is the association between position of
    radar (in degree) and the distance detected in that position.

    Args:
        df_radar_base:      data sent from distance radar component.
        df_distance_sensor: data sent from the distance radar sensor component.

    Return:
        A pd.Series. The index is the position of the radar base and the value is the distance deteced. 

    Note:
        The map is discrete. The value of index in the retured Series is integer.
    """



    df_sensor = df_distance_sensor
    df_base = df_radar_base

    df_sensor['timestamp'] = format_timestamp(df_sensor['timestamp'])
    df_base['timestamp']   = format_timestamp(df_base['timestamp'])

    df = pd.merge(df_sensor, df_base, on='timestamp', how='outer', suffixes=('_sensor','_base')).sort_values('timestamp')
    
    # smooth the distance.
#    window = int(df.shape[0] / df['pos'].notnull().sum())
#    df['avg_distance'] = df['distance'].rolling(window=window, min_periods=1).mean()
#    df['distance'] = df['distance'].combine_first(df['avg_distance'])
#    df = df.drop('avg_distance', axis=1)

    # clean the data
    df['distance'] = df['distance'].fillna(method='ffill')
    df['status']   = df['distance'].fillna(method='ffill')

    df_work = df[(df['pos'].notnull()) & (df['distance'].notnull())]

    # select useful information
    df_work = df_work[['timestamp','status','distance','pos','degree']]


    # create the distance map
    df_work['pos_bin'] = df_work['pos'].astype(int)

    ts_distance_map = df_work.gropuby(by='pos_bin')['distance'].mean().sort_index()

    return ts_distance_map





def retrieve_data(Q, data_handler):
    while not Q.empty():
        msg = Q.get()
        data_handler.update(msg)




class Controller:

    def __init__(self, radar_base=None, radar_distance_sensor=None, engine=None):
        assert isinstance(radar_base, ContinuousComponentWrapper)
        assert isinstance(radar_distance_sensor, ContinuousComponentWrapper)
        assert isinstance(engine, Engine)

        self._radar_base = radar_base
        self._radar_distance_sensor = radar_distance_sensor
        self._engine = engine

        self._components = ['radar_base','radar_distance_sensor','engin']

        self._comp_output_Q = {}
        self._comp_output_Q['radar_base'] = self._radar_base.output_Q
        self._comp_output_Q['radar_distance_sensor'] = selef._radar_distance_sensor.output_Q

        self._data_handler = {}
        self._data_handler['radar_base'] = RawDataHandler(name=self._radar_base.name, parser=self._radar_base.FORMAT, record_size=500)
        self._data_handler['radar_distance_sensor'] = RawDataHandler(name=self._radar_distance_sensor.name,parser=self._radar_distance_sensor.FORMAT, record_size=500)

                                



    def run(self):
        """
        The controller will analyze the data received from different components, make decisions to adjustment the status of
        the robot and send back commands to each component.
        """
        


        while True:


            # retrieve data from different component
            for item in self._components:
                retrieve_data(self._comp_output_Q[item], self._data_handler[item])


            # craete the distance map
            ts_distance_map = create_distance_map(df_radar_base, df_radar_distance_sensor)



            # analyze






