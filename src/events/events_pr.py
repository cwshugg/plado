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
    
    def poll_action(self):
        """
        Implementation of the abstract poll() function.
        """
        # retrieve the project and repository according to the config
        self.project = ado_find_project(self.config.get("project"))
        self.repo = ado_find_repo(self.project, self.config.get("repository"))

        # get all PRs from the repository
        self.prs = ado_repo_get_pullreqs(self.project, self.repo)

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

