import time
import multiprocessing as mp
import psutil
import os
import signal


from components import (DistanceRadarBaseComponent, DistanceRadarSensorComponent, WheelComponent, ContinuousComponentWrapper)
from engine import Engine
from controller import RawDataHandler

import xutils

if __name__ == '__main__':
    
    
    # set up radar base
    in_1 = 3
    in_2 = 5
    in_3 = 7
    in_4 = 11

    pins = [in_1, in_2, in_3, in_4 ]

    radar_base = DistanceRadarBaseComponent(name='radar_base', pins=pins, step_size=0.71, initial_pos=0, min_degree=-60, max_degree=40, delay=0.0025, delay_factor=5)
    radar_base.initialize()
    radar_base_datahandler = RawDataHandler(name=radar_base.name, parser=radar_base.FORMAT, record_size=1000)

    cmd_Q_base    = mp.Queue()
    output_Q_base = mp.Queue()

    cont_radar_base = ContinuousComponentWrapper(component=radar_base, cmd_Q=cmd_Q_base, output_Q=output_Q_base)


    # set up distance sensor
    pin_echo = 18
    pin_trig = 16

    cmd_Q_sensor = mp.Queue()
    output_Q_sensor = mp.Queue()

    distance_sensor = DistanceRadarSensorComponent(name='radar_distance_sensor', pin_echo=pin_echo, pin_trig=pin_trig, delay=0.0007)
    distance_sensor_datahandler = RawDataHandler(name=distance_sensor.name, parser=distance_sensor.FORMAT, record_size=2000)

    cont_distance_sensor = ContinuousComponentWrapper(component=distance_sensor, cmd_Q=cmd_Q_sensor, output_Q=output_Q_sensor)
    
    # set up wheels
    
    pin_signal_left = 13
    pin_signal_right = 15

    left_wheel_component  = WheelComponent(name='left_wheel',  mirror=False, pin_signal=pin_signal_left,  repeat=10, pulse=None, width=None, power=0.4)
    right_wheel_component = WheelComponent(name='right_wheel', mirror=True,  pin_signal=pin_signal_right, repeat=10, pulse=None, width=None, power=0.4)

    engine = Engine(left_wheel_comp=left_wheel_component, right_wheel_comp=right_wheel_component)



    # start all the components
    cont_radar_base.start()
    cont_distance_sensor.start()
    engine.start()


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
        _start = time.time()

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
        try:
            data4hist_distance_map = series2histdata(distance_map)
        except:
            #print(distance_map, distance_map.isnull().sum())
            print("[failed] Cannot create distance map")

        try:
            pass
#            plot_hist(data4hist_distance_map, pch='#',bincount=100)
        except Exception:
            pass
            print("[failed] Cannot plot distance map")

        print("time elapses: {}".format(time.time() - _start))

        # handle the input from the keyboard

        # When we read the key press, we will temporarily switch to the non-canonical mode
        # so that we can read the input from the keyboard char by char instead of waiting
        # for the new line character

        # this functionality is provided by the xutils.key_press_handler

        while True:
            __start = time.time()
            key_press = xutils.key_press_handler(timeout=25)

            print("key_press waiting time: {}".format(time.time() - __start))


            if key_press == 'q':
                print("Exiting system")
                pid = os.getpid()
                parent = psutil.Process(pid)
                children = parent.children(recursive=True)
                for process in children:
                    os.kill(process.pid, signal.SIGINT)

                os.kill(pid, signal.SIGINT)



            elif key_press is None:
                break

            elif key_press == xutils.UP_ARR:
                print(xutils.UP_ARR)
                engine.increase_speed(0.005) 
            elif key_press == xutils.DOWN_ARR:
                print(xutils.DOWN_ARR)
                engine.increase_speed(-0.005)
            elif key_press == xutils.LEFT_ARR:
                print(xutils.LEFT_ARR)
                engine.turn_left(scale=0.01, weight=0.2, period=0.3)
            elif key_press == xutils.RIGHT_ARR:
                print(xutils.RIGHT_ARR)
                engine.turn_right(scale=0.01, weight=0.2, period=0.3)
        
        engine.stop()




