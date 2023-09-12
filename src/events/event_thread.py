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

    def run(self):
        """
        The event thread's main function, invoked when the thread is started.
        """
        dbg_print("event", "Event thread activated.")

        # loop forever
        while True:
            # pop an event from the queue (wait if it's empty)
            e = self.equeue.pop(wait=True)

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
