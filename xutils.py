
import tty
import termios
import sys
import signal
import os

UP_ARR    = "__up_arrow__"
DOWN_ARR  = "__down_arrow__"
LEFT_ARR  = "__left_arrow__" 
RIGHT_ARR = "__right_arrow__"

def getchar():
    fd = sys.stdin.fileno()
    old_setting = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_setting)
    return ch




def arrow_key_handler():
    ch1 = getchar()
    ch2 = getchar()
    ch3 = getchar()

    if ord(ch1) == 27 and ord(ch2) == 91:
        val = ord(ch3)
        if val == 65:
            return UP_ARR
        elif val == 68:
            return LEFT_ARR
        elif val == 66:
            return DOWN_ARR
        elif val == 67:
            return RIGHT_ARR
        else:
            return None
        

def key_press_handler():
    ch = getchar()

    if ord(ch) == 27:
        ch2 = getchar()
        if ord(ch2) ==  91:
            ch3 = getchar()
            val = ord(ch3)
            if val == 65:
                return UP_ARR
            elif val == 68:
                return LEFT_ARR
            elif val == 66:
                return DOWN_ARR
            elif val == 67:
                return RIGHT_ARR
            else:
                return None

    else:
        return ch




def _INT_handler(signal, frame):
    print("inside _INT_handler")
    raise KeyboardInterrupt

def kill_current_process():
    os.kill(os.getpid, signal.SIGINT.value)


if __name__ == '__main__':
    pid = os.getpid()
    SIGINT = signal.SIGINT.value
    while True:
        key_press = key_press_handler()

        if key_press == 'q':
            print("exiting")
            os.kill(pid, SIGINT)
            break
        else:
            print(key_press)

