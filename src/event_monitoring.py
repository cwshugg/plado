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
from events.events_branch import *
from debug import dbg_print
from utils.utils import *
from utils.colors import *
from utils.storage import *

# Globals
event_classes = { # map of type names to classes
    "pr_create":                [Event_PR_Create, EventConfig_PR_Create],
    "pr_draft_on":              [Event_PR_Draft_On, EventConfig_PR_Draft_On],
    "pr_draft_off":             [Event_PR_Draft_Off, EventConfig_PR_Draft_Off],
    "pr_commit_new_src":        [Event_PR_Commit_New_Src, EventConfig_PR_Commit_New_Src],
    "pr_commit_new_dst":        [Event_PR_Commit_New_Dst, EventConfig_PR_Commit_New_Dst],
    "pr_status_change":         [Event_PR_Status_Change, EventConfig_PR_Status_Change],
    "pr_reviewer_added":        [Event_PR_Reviewer_Added, EventConfig_PR_Reviewer_Added],
    "pr_reviewer_voted":        [Event_PR_Reviewer_Voted, EventConfig_PR_Reviewer_Voted],
    "pr_comment_added":         [Event_PR_Comment_Added, EventConfig_PR_Comment_Added],
    "pr_comment_edited":        [Event_PR_Comment_Edited, EventConfig_PR_Comment_Edited],
    "pr_comment_liked":         [Event_PR_Comment_Liked, EventConfig_PR_Comment_Liked],
    "pr_comment_unliked":       [Event_PR_Comment_Unliked, EventConfig_PR_Comment_Unliked],
    "pr_comment_resolved":      [Event_PR_Comment_Resolved, EventConfig_PR_Comment_Resolved],
    "pr_comment_unresolved":    [Event_PR_Comment_Unresolved, EventConfig_PR_Comment_Unresolved],
    "branch_commit_new":        [Event_Branch_Commit_New, EventConfig_Branch_Commit_New],
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
    print("Initialized %d event(s). Monitoring..." % len(events))

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
        now = datetime.now(tz=timezone.utc)
        nowstr = now.strftime("%Y-%m-%d %H:%M:%S %p")
        dbg_print("event", "[%s UTC] %s" % (nowstr, msg))
    
    # ensure the poll rate is greater than zero
    poll_rate = config.get("monitor_poll_rate")
    if poll_rate <= 0:
        panic("The poll rate (%smonitor_poll_rate%s) must be greater than zero." %
              (color("config_field_name"), color("none")))
    
    # attempt to read a file from storage containing the last-polled datetime
    last_poll = storage_obj_read("em_last_poll")
    if last_poll is not None:
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

        # wait until all threads are finished with their work and are once again
        # waiting for the queue to be filled
        for et in ethreads:
            et.wait_is_waiting_on_queue()
        em_dbg_print("All events processed and all threads are waiting.")

        # now that we know all threads are asleep and all events are processed,
        # run each events' cleanup routine
        for e in events:
            e.cleanup()

        # update the last-poll time in storage, then sleep for the configured
        # amount of time
        storage_obj_write("em_last_poll", datetime.now(tz=timezone.utc))
        time.sleep(poll_rate)

