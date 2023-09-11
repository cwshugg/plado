# This module defines a generic Event object, which is the parent of all unique
# event objects.

# Imports
import os
import sys
import time
from datetime import datetime

# Library path setup
srcdir = os.path.realpath(os.path.dirname(__file__))
if srcdir not in sys.path:
    sys.path.append(srcdir)

# Tool imports
from config import config_load
from events.event import *
from events.event_config import *
from events.event_queue import EventQueue
from events.event_thread import EventThread
from events.events_pr import *
from debug import dbg_print
from utils.nugget import Nugget
from utils.utils import *
from utils.colors import *

# Globals
event_classes = { # map of type names to classes
    "pr_create": [Event_PR_Create, EventConfig_PR_Create]
}
events = []

def em_create_event(edata: dict):
    """
    Takes in a JSON dictionary of event information and uses it to locate an
    appropriate event class to initialize. Creates an Event object and returns
    it.
    """
    # first, parse the data as a base-level event config, to ensure the
    # necessary information is present
    ec = EventConfig()
    ec.parse_json(edata)

    # examine the event type and ensure it's a known type
    ec_type = ec.get("type").lower()
    if ec_type not in event_classes:
        panic("Unrecognized event type: \"%s\"." % ec_type)

    dbg_print("event", "Initializing event of type \"%s\"." % ec_type)
    [cls, config_cls] = event_classes[ec_type]
    ec = config_cls()
    ec.parse_json(edata)
    e = cls(ec)
    return e

def em_init():
    """
    Initializes and prepares for event monitoring mode.
    """
    # first, retrieve the config object and look for the events field
    config = config_load()
    evs = config.get("monitor_events")
    if len(evs) == 0:
        panic("You have not specified any events to monitor.")

    # otherwise, iterate through the events in the list and parse them as event
    # config objects. Then, create Event objects with each config
    global events
    events = []
    for entry in evs:
        events.append(em_create_event(entry))
    dbg_print("event", "Initialized %d event(s)." % len(events))

def em_main():
    """
    The "main" function for event monitoring mode. Repeatedly loops and
    spawns threads to check individual events' statuses.
    """
    config = config_load()
    global events
    dbg_print("event", "Beginning event monitoring.")

    # Helper function for debugging prints with a date/time prefix
    def em_dbg_print(msg: str):
        now = datetime.now()
        nowstr = now.strftime("%Y-%m-%d %H:%M:%S %p")
        dbg_print("event", "[%s] %s" % (nowstr, msg))
    
    # ensure the poll rate is greater than zero
    poll_rate = config.get("monitor_poll_rate")
    if poll_rate <= 0:
        panic("The poll rate (%smonitor_poll_rate%s) must be greater than zero." %
              (color("config_field_name"), color("none")))

    # create a nugget to use for keeping track of the last time we iterated in
    # the below loop. If we can read a value in from a previous run, update all
    # events' 'last_poll' values to reflect it
    ngt_last_poll = Nugget("em_last_poll", [int])
    last_poll = ngt_last_poll.read()
    if last_poll is not None:
        last_poll = datetime.fromtimestamp(last_poll)
        for e in events:
            e.set_last_poll_time(last_poll)
        # write the last-poll time out to debug
        dbg_print("event", "Last poll time: %s" %
                  last_poll.strftime("%Y-%m-%d %H:%M:%S %p"))
    
    # ensure the number of threads is greater than zero
    ethreads_len = config.get("monitor_threads")
    if ethreads_len <= 0:
        panic("The number of event monitoring threads (%smonitor_threads%s) "
              "must be greater than zero." %
              (color("config_field_name"), color("none")))

    # create an event queue and the configured number of event threads
    equeue = EventQueue()
    ethreads = []
    for i in range(ethreads_len):
        et = EventThread(equeue)
        ethreads.append(et)
        et.start()

    while True:
        em_dbg_print("Polling for events.")

        # submit each event to the queue for examination by the worker threads
        for e in events:
            equeue.push(e)

        # wait until all queue entries have been processed
        while equeue.size() > 0:
            pass

        # update the last-poll nuggest, then sleep for the configured time
        ngt_last_poll.write(int(datetime.now().timestamp()))
        time.sleep(poll_rate)

