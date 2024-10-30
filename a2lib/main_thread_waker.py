"""A static/singleton class for waking the main thread _once_."""
import os
import signal


class WakingMainThread(Exception):
    pass

class MainThreadWaker(object):
    """A static/singleton class for waking the main thread _once_.
    
    See assignment description, as well as the sample code below, to figure
    out how/why to use this."""
    _woken = False

    @classmethod
    def register(cls):
        signal.signal(signal.SIGILL, cls._wake_handler)

    @classmethod
    def main_awake(cls):
        cls._woken = True

    @staticmethod
    def wake_main_thread():
        os.kill(os.getpid(), signal.SIGILL)

    @classmethod
    def _wake_handler(cls, _1, _2):
        print("Waking called.")
        if not cls._woken:
            print("Waking main thread.")
            cls._woken = True
            raise WakingMainThread()
        else:
            print("Main thread already woken.")