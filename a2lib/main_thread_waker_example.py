import sys
import time
from threading import Thread

from consolelib import *
from main_thread_waker import MainThreadWaker, WakingMainThread


def main(args):
    # Register the main thread waker mechanism
    MainThreadWaker.register()

    # Create a thread that will wake the main thread in 5 seconds
    def wake_main_example():
        time.sleep(5)
        MainThreadWaker.wake_main_thread()
    waking_thread = Thread(target=wake_main_example)
    waking_thread.start()

    try:
        # Do a blocking input
        msg = input("> ")
        print(msg)
    except WakingMainThread:
        # The waker works by forcing the main thread to raise the WakingMainThread 
        # exception regardless of if it's blocking for anything. Catch the
        # exception to safely break out. 
        #
        # (In your assignment code you'll should only need to do this once
        # when your client is disconnecting from the server.)
        print("Main thread woken by other thread.")
    finally:
        # Whether we got input, or were woken up, it's best to let the waker 
        # know that we're alive to avoid more exceptions being thrown.
        MainThreadWaker.main_awake()

    # Wait for the waking thread to complete (if we got input in time) to 
    # illustrate that it will only throw the exception once.
    waking_thread.join()
    print("Waking thread joined.")

    # An additonal sleep to show that the join means the created thread has
    # totally stopped.
    time.sleep(5)

    print("Exiting successfully.")
    sys.stdout.flush()


if __name__ == "__main__":
    main(sys.argv[1:])
