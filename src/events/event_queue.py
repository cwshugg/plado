# This module defines an queue, used to submit Event objects for examination by
# worker threads (which are also defined in this module).
#
# Each worker thread, when not processing an event, must wait for the event
# queue to be filled. Once full, the thread wake up and pop an event off the
# queue to process.
#
# When processing an event, the worker thread must invoke the event's poll()
# function to determine if the event has occurred. If poll() succeeds and data
# is returned, the worker thread will spawn subprocesses for each of the event's
# configured jobs.

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
from debug import dbg_print

class EventQueue():
    """
    A class representing a thread-safe queue that holds Event objects.
    This uses a mutex lock paired with a condition variable to ensure mutual
    exclusion when accessing the underlying queue. The condition variable is
    used to wake up threads when a new event has been pushed to the queue for
    processing.
    """
    def __init__(self):
        """
        Constructor. Initializes the inner queue and all thread synchronization
        data structures.
        """
        self.queue = []
        self.lock = threading.Lock()
        self.condition = threading.Condition(lock=self.lock)

    def push(self, event: Event):
        """
        Pushes a new event object onto the queue for processing. One or more
        worker threads are woken up to process the new event.
        """
        self.lock.acquire()         # acquire lock
        self.queue.append(event)    # append to the END
        self.condition.notify()     # wake a single thread
        self.lock.release()         # release lock
    
    def pop(self, wait=False):
        """
        Pops an event from the queue for processing.
        If no more elements are on the queue, this returns None.
        If 'wait' is True, the calling thread will block if the queue is empty,
        until notified.
        """
        self.lock.acquire()
        
        # if specified, block until the queue has something in it
        while wait and len(self.queue) == 0:
            self.condition.wait()

        # if the queue is empty
        if len(self.queue) == 0:
            self.lock.release()
            return None

        # otherwise, pop the next queue entry and release the lock
        result = self.queue.pop(0)
        self.lock.release()
        return result

    def size(self):
        """
        Retrieves and returns the current queue size.
        """
        self.lock.acquire()
        s = len(self.queue)
        self.lock.release()
        return s

    def wipe(self):
        """
        Removes all events from the event queue.
        """
        self.lock.acquire()
        self.queue = []
        self.lock.release()

