# This module defines a generic Event object, which is the parent of all unique
# event objects.

# Imports
import os
import sys

# Library path setup
srcdir = os.path.realpath(os.path.dirname(__file__))
if srcdir not in sys.path:
    sys.path.append(srcdir)

# Tool imports
from config import config_load
from events.event import *
from events.event_config import *
from events.events_pr import *
from debug import dbg_print
from utils.utils import *

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

