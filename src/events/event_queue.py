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
from debug import dbg_print

class EventQueue():
    """
    A class representing a thread-safe queue that holds Event objects.
    """
    def __init__(self):
        """
        Constructor. Initializes the inner queue and all thread synchronization
        data structures.
        """
        # TODO

