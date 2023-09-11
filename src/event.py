# This module defines a generic Event object, which is the parent of all unique
# event objects.

# Imports
import os
import sys
import abc

# Library path setup
srcdir = os.path.realpath(os.path.dirname(__file__))
if srcdir not in sys.path:
    sys.path.append(srcdir)

# Tool imports
from config import EventConfig, EventJobConfig
from debug import dbg_print
from utils.utils import *


# ================================ Job Class ================================= #
class EventJob():
    """
    Class representing a single job to execute when an event fires.
    """
    def __init__(self, conf: EventJobConfig):
        self.config = conf


# =============================== Event Class ================================ #
class Event(abc.ABC):
    """
    A class that represents a single event to be monitored. Contains jobs to
    execute when the event fires.
    """
    def __init__(self, conf: EventConfig):
        self.config = conf

        # use the event's name or type as a name for error/debug messages
        name = self.config.get("name")
        if name is None:
            name = self.config.get("type")
        
        # if no jobs are given, complain
        jobs = self.config.get("jobs")
        jobs_len = len(jobs)
        if jobs_len == 0:
            panic("You must specify at least one job for each event. "
                  "(Event \"%s\" has no jobs.)" % name)

        # parse each job into a job config
        dbg_print("event", "Found %d job(s) for event \"%s\". Parsing." %
                  (jobs_len, name))
        self.jobs = []
        for jdata in jobs:
            jc = EventJobConfig()
            jc.parse_json(jdata)
            self.jobs.append(EventJob(jc))
        
