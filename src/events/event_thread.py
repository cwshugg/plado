# This module defines event threads, which are responsible for repeatedly
# examining a given event queue, popping events off of it, and processing those
# events. These threads are the ones that interact with the Event objects and
# fire their jobs when necessary.

# Imports
import os
import sys
import threading

# Library path setup
srcdir = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))
if srcdir not in sys.path:
    sys.path.append(srcdir)

# Tool imports
from events.event import Event
from events.event_queue import EventQueue
from debug import dbg_print

class EventThread(threading.Thread):
    """
    A class representing a single Event thread. These threads are given an
    event queue and are responsible for popping Events and processing them as
    they appear.
    """
    def __init__(self, queue: EventQueue):
        """
        Constructor. Takes in the event queue.
        """
        super().__init__(target=self.run)
        self.equeue = queue
        self.is_waiting_on_queue = False
        self.is_waiting_on_queue_lock = threading.Lock()
        self.is_waiting_on_queue_condition = threading.Condition(lock=self.is_waiting_on_queue_lock)

    def get_is_waiting_on_queue(self):
        """
        Uses a mutex lock to safely extract the boolean flag indicating whether
        or not the thread is currently waiting on the event queue.

        This is used by the main thread to guage when these event threads are
        finished with their work and are waiting for more.
        """
        self.is_waiting_on_queue_lock.acquire()
        val = self.is_waiting_on_queue
        self.is_waiting_on_queue_lock.release()
        return val

    def set_is_waiting_on_queue(self, val: bool):
        """
        Uses a mutex lock to safely set the internal 'is_waiting_on_queue' flag.
        """
        self.is_waiting_on_queue_lock.acquire()
        self.is_waiting_on_queue = val
        self.is_waiting_on_queue_condition.notify()
        self.is_waiting_on_queue_lock.release()

    def wait_is_waiting_on_queue(self):
        """
        Waits on an internal condition variable until 'is_waiting_on_queue'
        is set to True.
        """
        self.is_waiting_on_queue_lock.acquire()
        while not self.is_waiting_on_queue:
            self.is_waiting_on_queue_condition.wait()
        self.is_waiting_on_queue_lock.release()
    
    def run(self):
        """
        The event thread's main function, invoked when the thread is started.
        """
        dbg_print("event", "Event thread activated.")

        # loop forever
        while True:
            # pop an event from the queue (wait on the queue's internal
            # condition variable)
            self.set_is_waiting_on_queue(True)
            dbg_print("event", "Waiting on event queue.")
            e = self.equeue.pop(wait=True)
            self.set_is_waiting_on_queue(False)
            
            dbg_print("event", "Found an event to process: \"%s\"" %
                      e.typename())

            # poll the event - if there's nothing new, re-loop
            result = e.poll()
            if result is None:
                continue
            
            ename = e.config.get("name")
            if ename is None:
                ename = e.typename()
            dbg_print("event", "Event \"%s\" has occurred." % ename)
            
            # otherwise, iterate through the returned data and fire all of the
            # event's jobs
            for entry in result:
                for job in e.jobs:
                    # spawn a subprocess to handle the job
                    job.fire(entry, wait=False)

            # with all subprocesses spawned, wait for them all to complete
            for job in e.jobs:
                job.reap()
            dbg_print("event", "Reaped %d subprocesses for event \"%s\"." %
                      (len(e.jobs), ename))

