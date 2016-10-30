




import time
import multiprocessing as mp


from components import (DistanceRadarBaseComponent, DistanceRadarSensorComponent, WheelComponent, ContinuousComponentWrapper)
from engine import Engine
from controller import RawDataHandler


if __name__ == '__main__':
    
    
    # set up the radar base
    in_1 = 3
    in_2 = 5
    in_3 = 7
    in_4 = 11

    pins = [in_1, in_2, in_3, in_4 ]

    radar_base = DistanceRadarBaseComponent(name='radar_base', pins=pins, step_size=0.71, initial_pos=0, min_degree=-60, max_degree=40, delay=0.0035)
    radar_base.initialize()
    radar_base_datahandler = RawDataHandler(name=radar_base.name, parser=radar_base.FORMAT, record_size=1000)

    cmd_Q_base    = mp.Queue()
    output_Q_base = mp.Queue()

    cont_radar_base = ContinuousComponentWrapper(component=radar_base, cmd_Q=cmd_Q_base, output_Q=output_Q_base)


    # set up the distance sensor
    pin_echo = 18
    pin_trig = 16

    cmd_Q_sensor = mp.Queue()
    output_Q_sensor = mp.Queue()

    distance_sensor = DistanceRadarSensorComponent(name='radar_distance_sensor', pin_echo=pin_echo, pin_trig=pin_trig, delay=0.00007)
    distance_sensor_datahandler = RawDataHandler(name=distance_sensor.name, parser=distance_sensor.FORMAT, record_size=10000)

    cont_distance_sensor = ContinuousComponentWrapper(component=distance_sensor, cmd_Q=cmd_Q_sensor, output_Q=output_Q_sensor)
    
    
    pin_signal_left = 13
    pin_signal_right = 15

    left_wheel_component  = WheelComponent(name='left_wheel',  mirror=False, pin_signal=pin_signal_left,  repeat=30, pulse=None, width=None)
    right_wheel_component = WheelComponent(name='right_wheel', mirror=True,  pin_signal=pin_signal_right, repeat=30, pulse=None, width=None)

    engine = Engine(left_wheel_comp=left_wheel_component, right_wheel_comp=right_wheel_component)



    # start all the components
    cont_radar_base.start()
    cont_distance_sensor.start()

#    engine.start()

    # control ??
    import controller as ctl
    from bashplotlib.histogram import plot_hist
    import numpy as np

    def series2histdata(ts):
        if ts.isnull().sum() > 30:
            return [0]
        _ts = (ts * 100).astype(int)
        n = _ts.sum()
        out = np.empty(n)
        i = 0
        for item in _ts.index:
            count = _ts.loc[item]
            out[i: (i+count)] = item
            i += count

        return out
            

            

    while True:

        while not output_Q_sensor.empty():
            msg = output_Q_sensor.get()
            distance_sensor_datahandler.update(msg)
#            print(msg)

        while not output_Q_base.empty():
            msg = output_Q_base.get()
            radar_base_datahandler.update(msg)
#            print(msg)
        df_base = radar_base_datahandler.data
        df_sensor = distance_sensor_datahandler.data

        distance_map = ctl.create_distance_map(df_base, df_sensor)
        data4hist_distance_map = series2histdata(distance_map)

#        print(distance_map.head(20))
#        time.sleep(1)
#        print(distance_map.iloc[20:40])
#        time.sleep(1)
#        print(distance_map.iloc[40:60])
#        time.sleep(1)
#        print(distance_map.iloc[60:80])
#        time.sleep(1)
#        print(distance_map.iloc[80:99])
#        time.sleep(1)
        try:
            plot_hist(data4hist_distance_map, pch='#',bincount=100)
        except Exception:
            pass
        for idx in distance_map.index:
            print('{:2d}:{:0.2f}'.format(idx, distance_map[idx]), " ", end="")
        print()
        print()

#        print('\n'*10)
            
#        engine.stop() 
#        time.sleep(5)
#        print('engine increases speed')
#        engine.increase_speed(0.2)
        


