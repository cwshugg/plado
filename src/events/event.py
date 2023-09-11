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
from config import EventConfig, EventFilterConfig, EventJobConfig
from debug import dbg_print
from utils.utils import *


# ================================ Job Class ================================= #
class EventJob():
    """
    Class representing a single job to execute when an event fires.
    """
    def __init__(self, conf: EventJobConfig):
        self.config = conf


# =============================== Filter Class =============================== #
class EventFilter():
    """
    Class representing a single filter for a monitored event.
    """
    def __init__(self, conf: EventFilterConfig):
        self.config = conf


# =============================== Event Class ================================ #
class Event(abc.ABC):
    """
    A class that represents a single event to be monitored. Contains filters
    and jobs to execute when the event fires.
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
        
        # if filters are given, parse them
        filters = self.config.get("filters")
        filters_len = len(filters)
        self.filters = []
        if filters_len > 0:
            dbg_print("event", "Found %d filter(s) for event \"%s\". Parsing." %
                      (filters_len, name))
            for fdata in filters:
                fc = EventFilterConfig()
                fc.parse_json(fdata)
                self.filters.append(EventFilter(fc))
        else:
            dbg_print("event", "Found no filters for event \"%s\"." % name)


