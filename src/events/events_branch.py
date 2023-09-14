# This module defines events related to ADO git branches.

# Imports
import os
import sys
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


# ======================= Generic Branch Event Objects ======================= #
class EventConfig_Branch(EventConfig):
    """
    An extension of the EventConfig class specific to branches.
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
                description="The name or ID of the project that contains the branch.",
                required=True
            ),
            "repository": ConfigField(
                "repository",
                [str],
                description="The name or ID of the repository that contains the branch.",
                required=True
            ),
            "branch": ConfigField(
                "branch",
                [str],
                description="The name or ID of the branch to track.",
                required=False,
                default=None
            ),
        })

class Event_Branch(Event):
    """
    An extension of the Event class specific to branches.
    """
    def __init__(self, conf: EventConfig_Branch):
        """
        Constructor.
        """
        super().__init__(conf)
        # retrieve the project and repository according to the config
        self.project = ado_find_project(self.config.get("project"))
        self.repo = ado_find_repo(self.project, self.config.get("repository"))

        # retrieve the branch
        self.branch = None
        config_branch = self.config.get("branch")
        if config_branch is not None:
            self.branch = ado_find_branch(self.project, self.repo, config_branch)

        # initialize branch storage fields
        self.branches = []
        self.branches_backup_key = "project_%s_repo_%s_branches" % \
                             (self.project.id, self.repo.id)
        self.branches_backups = None

    def cmp_branch(self, br1, br2):
        """
        Takes in two branch objects and returns True if they are the same branch.
        """
        return br1.name.strip() == br2.name.strip()

    def filtered_branches(self):
        """
        Used to determine what branches to examine during loops in poll_action().
        Returns either ALL branches in the list, or a list containing only the
        branch specified in the config.
        """
        if self.branch is None:
            return self.branches
        
        # if a branch WAS specified in the config, search for it and return
        # *only* that branch in a list
        for br in self.branches:
            if self.cmp_branch(self.branch, br):
                return [br]
        return []

    def poll_action(self):
        """
        Implementation of the abstract poll() function.
        """
        # get all branches from the repository
        self.branches = ado_repo_get_branches(self.project, self.repo)

        # retrieve the older version of branch info from disk
        self.branches_backups = storage_obj_read(self.branches_backup_key, lock=True)

        # this is an intermediate implementation - the subclasses will
        # carry on from this point (return None)
        return None

    def cleanup_action(self):
        """
        Overridden cleanup_action().
        """
        # convert the list of branches to a dictionary, then write to disk, for use
        # during the next event poll
        brs = {}
        for br in self.branches:
            brs[br.name] = br
        storage_obj_write(self.branches_backup_key, brs)


# ============================ Branch New Commit ============================= #
class EventConfig_Branch_Commit_New(EventConfig_Branch):
    """
    An extension of the EventConfig_Branch class specific for a new branch commit.
    """

class Event_Branch_Commit_New(Event_Branch):
    """
    An extension of the Event_Branch class specific for a new branch commit.
    """
    def poll_action(self):
        """
        Overridden poll_action().
        """
        super().poll_action()
        # if we don't have a backup of branch data from a previous poll, we
        # can't yet detect if this event has happened
        if self.branches_backups is None:
            return None

        # for each pull request currently active
        results = []
        for br in self.filtered_branches():
            # if the branch was *just* created, and we don't have a previous
            # record of it, ignore it
            if br.name not in self.branches_backups:
                continue
            br_old = self.branches_backups[br.name]

            # otherwise, compare the two versions's latest commits
            commit_new = br.commit
            commit_old = br_old.commit

            self.dbg_print("Branch %s%s%s latest commit: old=%s%s%s, new=%s%s%s." %
                           (color("branch"), br.name, color("none"),
                            color(commit_new.commit_id), commit_new.commit_id, color("none"),
                            color(commit_old.commit_id), commit_old.commit_id, color("none")))


            # if the IDs differ, we've got a new commit
            if commit_new.commit_id != commit_old.commit_id:
                results.append(br)

        results_len = len(results)
        self.dbg_print("Found %s branch(es) with new commits." %
                       ("no" if results_len == 0 else str(results_len)))
        return None if results_len == 0 else results

