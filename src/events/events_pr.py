# This module defines events related to ADO Pull Request.

# Imports
import os
import sys
import dateutil.parser
from datetime import datetime, timezone

# Library path setup
srcdir = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))
if srcdir not in sys.path:
    sys.path.append(srcdir)

# Tool imports
from events.event_config import *
from events.event import *
from ado import *
from debug import dbg_print
from utils.utils import *
from utils.storage import *


# ========================= Generic PR Event Objects ========================= #
class EventConfig_PR(EventConfig):
    """
    An extension of the EventConfig class specific to pull requests.
    This adds additional config fields that are required for this event.
    """
    def __init__(self):
        """
        Constructor.
        """
        super().__init__()
        self.fields.update({
            "project": ConfigField(
                "project",
                [str],
                description="The name or ID of the project that contains the PR.",
                required=True
            ),
            "repository": ConfigField(
                "repository",
                [str],
                description="The name or ID of the repository that contains the PR.",
                required=True
            )
        })

class Event_PR(Event):
    """
    An extension of the Event class specific to pull requests.
    """
    def __init__(self, conf: EventConfig_PR):
        """
        Constructor.
        """
        super().__init__(conf)
        # retrieve the project and repository according to the config
        self.project = ado_find_project(self.config.get("project"))
        self.repo = ado_find_repo(self.project, self.config.get("repository"))

        # initialize PR-related fields
        self.prs = []
        self.pr_backup_key = "project_%s_repo_%s_pullreqs" % \
                             (self.project.id, self.repo.id)
        self.pr_backups = None

    def poll(self):
        """
        Wrapper for poll() that updates the PR backups in storage.
        """
        result = super().poll()
        # convert the list of PRs to a dictionary, then write to disk
        prs = {}
        for pr in self.prs:
            prs[pr.code_review_id] = pr
        storage_obj_write(self.pr_backup_key, prs, lock=True)
        return result
    
    def poll_action(self):
        """
        Implementation of the abstract poll() function.
        """
        # get all PRs from the repository
        self.prs = ado_repo_get_pullreqs(self.project, self.repo)

        # iterate through all PRs and load previously-stored versions of them
        # from the last poll
        self.pr_backups = storage_obj_read(self.pr_backup_key, lock=True)

        # this is an intermediate implementation - the subclasses will
        # carry on from this point (return None)
        return None


# =============================== PR Creation ================================ #
class EventConfig_PR_Create(EventConfig_PR):
    """
    An extension of the EventConfig_PR class specific for PR creation.
    """

class Event_PR_Create(Event_PR):
    """
    An extension of the Event_PR class specific for PR creation.
    """
    def poll_action(self):
        super().poll_action()
        new_prs = []
        new_prs_len = 0
        for pr in self.prs:
            pr.creation_date = pr.creation_date.replace(tzinfo=timezone.utc)
            creation = pr.creation_date
            
            # compute the difference, in seconds, between the two timestamps
            diff = self.get_last_poll_time().timestamp() - creation.timestamp()
            self.dbg_print("PR-%d was created on: [%s] (%d seconds %s last poll)." %
                           (pr.code_review_id,
                            creation.strftime("%Y-%m-%d %H:%M:%S %p"),
                            abs(diff), "after" if diff < 0 else "before"))

            # if the creation date is more recent than the last-polled time,
            # add it to the results list
            if diff < 0:
                new_prs.append(pr.as_dict())
                new_prs_len += 1

        # if PRs were collected, return them (otherwise return None)
        return None if new_prs_len == 0 else new_prs


# ============================= PR Draft Enable ============================== #
class EventConfig_PR_Draft_On(EventConfig_PR):
    """
    An extension of the EventConfig_PR class specific for a PR's draft mode
    being enabled.
    """

class Event_PR_Draft_On(Event_PR):
    """
    An extension of the Event_PR class specific for a PR's draft mode being
    enabled.
    """
    def poll_action(self):
        super().poll_action()
        # if we don't have a backup of PR data from a previous poll, we can't
        # yet detect if this event has happened
        if self.pr_backups is None:
            return None

        results = []
        results_len = 0
        
        self.dbg_print("TODO - IMPLEMENT A WAY FOR ALL PR THREADS TO SHARE THE "
                       "SAME COPY OF PR BACKUPS, SO THEY EACH DON'T WRITE EVERY "
                       "TIME MAYBE")
        self.dbg_print("OR IF NOT THAT, AT LEAST MAKE THEM USE A LOCK TO PREVENT "
                       "THE SAME FILE FROM BEING WRITTEN SIMULTANEOUSLY.")
                       

