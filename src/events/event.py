# This module defines a generic Event object, which is the parent of all unique
# event objects.

# Imports
import os
import sys
import abc
from datetime import datetime, timezone
import subprocess
import json

# Library path setup
srcdir = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))
if srcdir not in sys.path:
    sys.path.append(srcdir)

# Tool imports
from events.event_config import *
from debug import dbg_print
from utils.utils import *


class EventJob():
    """
    Class representing a single job to execute when an event fires.
    """
    def __init__(self, conf: EventJobConfig):
        """
        Constructor for the event job class.
        """
        self.config = conf
        self.process = None

    def reap(self):
        """
        Waits for the subprocess to complete and returns a CompletedProcess
        object.
        """
        assert self.process is not None, "No subprocess exists!"
        try:
            result = self.process.wait(timeout=self.config.get("timeout"))
            return result
        except subprocess.TimeoutExpired as e:
            dbg_print("event", "Subprocess timed out while waiting.")
            self.process.kill()
        self.process = None

    def fire(self, event_data: dict, wait=False):
        """
        Takes in a dictionary of event data (from an event that occurred) and
        launches the job's as a subprocess. The event data is converted to a
        JSON string and passed to the subprocess via stdin.
        If `wait` is set to True, this function will invoke self.reap(), making
        the caller block until the subprocess exits or times out.
        Otherwise, the return value from Popen() will be returned and the
        caller will not block.
        """
        # choose a working directory from which to launch the job
        run_dir = self.config.get("run_dir")
        if run_dir is None:
            run_dir = os.path.expandvars("${HOME}")
        
        # write debug message
        name = self.config.get("name")
        if name is None:
            name = self.__class__.__name__
        args = self.config.get("args")
        dbg_print("event", "Firing job \"%s\": %s" % (name, args))

        # spawn the process in the correct working directory, and hook up its
        # input and output streams to pipes, connected to this process (the
        # parent)
        self.process = subprocess.Popen(args,
                                        cwd=run_dir,
                                        stdin=subprocess.PIPE)
        
        # write the event data as a JSON string into the process' stdin
        try:
            dbg_print("event", "Sending JSON payload to subprocess.")
            payload = json.dumps(event_data)
            self.process.communicate(input=json.dumps(payload).encode(),
                                     timeout=self.config.get("timeout"))
        except subprocess.TimeoutExpired as e:
            dbg_print("event", "Subprocess timeouted out while writing JSON payload.")
            self.process.kill()
            self.reap()

        
        # wait for the process (if specified)
        if wait:
            return self.reap()
        return self.process

class Event(abc.ABC):
    """
    A class that represents a single event to be monitored. Contains jobs to
    execute when the event fires.
    """
    def __init__(self, conf: EventConfig):
        """
        Constructor for the Event object. Loads in the config and attempts to
        parse any nested configuration objects.
        """
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

        # lastly, initialize a timestamp for each event object to know
        # how long ago its previous call to poll() was. This is handy for
        # some time-sensitive polls that might, for example, look at
        # timestamps in ADO to determine if a new update has occurred since
        # its last poll
        self.last_poll = datetime.now()
        self.last_poll.replace(tzinfo=timezone.utc)

    def dbg_print(self, msg: str):
        """
        Wrapper for dbg_print() that adds a handy prefix to indicate what event
        the message is coming from.
        """
        name = self.config.get("name")
        if name is None:
            name = self.config.get("type")
        dbg_print("event", "[%s] %s" % (name, msg))

    def get_last_poll_time(self):
        """
        Returns the timestamp at which this event was last polled.
        """
        return self.last_poll.replace(tzinfo=timezone.utc)

    def set_last_poll_time(self, dt: datetime):
        """
        Updates the event's last-polled timestamp.
        """
        self.last_poll = dt.replace(tzinfo=timezone.utc)

    def poll(self):
        """
        A wrapper around poll_action() that maintains a 'last_poll' value, which
        tracks the last time the event was polled.
        """
        # invoke the abstract method poll_action() (where subclasses will
        # implement their custom logic)
        result = self.poll_action()

        # update last-polled time to be now, in UTC
        self.set_last_poll_time(datetime.now())
        return result
    
    @abc.abstractmethod
    def poll_action(self):
        """
        Communicates with ADO to determine if this event has occurred. If it
        has occurred, this returns with one or more collections of event data
        retrieved from ADO. Otherwise, None is returned.
        If this function returns data, the caller should save this data and
        invoke each job associated with the event once for EVERY event data
        returned.

        For example: if an event is tracking pull requests being created,
        this function might return a list of pull request information:
            
            [
                {"pull_request_id": 12345, ...},
                {"pull_request_id": 12346, ...}
            ]

        Let's say this event has three configured jobs. The caller should take
        *each* pull request data object and fire each of those three jobs once
        for every pull request. This would result in each job being executed
        twice, for a total of six different programs being run.
        """
        return None

