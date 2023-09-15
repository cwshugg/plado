# This module defines events related to ADO work items.

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


# ============================= Generic WI Event ============================= #
class EventConfig_WI(EventConfig):
    """
    An extension of the EventConfig class specific to work items.
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
                description="The name or ID of the project that contains the work items.",
                required=True
            ),
            "teams": ConfigField(
                "teams",
                [list],
                description="The names or IDs of the teams whose work items to track.",
                required=False,
                default=None
            ),
            "work_items": ConfigField(
                "work_items",
                [list],
                description="A list of work item IDs to track.",
                required=False,
                default=None
            ),
        })

class Event_WI(Event):
    """
    An extension of the Event class specific to branches.
    """
    def __init__(self, conf: EventConfig_WI):
        """
        Constructor.
        """
        super().__init__(conf)
        # retrieve the project according to the config
        self.project = ado_find_project(self.config.get("project"))

        self.wi_ids = []
        self.wi_ids_backup_key = "project_%s_workitems_ids" % self.project.id
        self.wi_backup_key_fmt = "project_%s_workitems_" % self.project.id

    def load_wi_ids(self):
        """
        Retrieves the list of work item IDs stored to disk. Returns None or an
        array of IDs.
        """
        return storage_obj_read(self.wi_ids_backup_key, lock=True)

    def save_wi_id(self, wid):
        """
        Saves a work item ID to the global backup object.
        """
        ids = storage_obj_read(self.wi_ids_backup_key, lock=True)
        if wid not in ids:
            ids.append(wid)
            ids = storage_obj_write(self.wi_ids_backup_key, lock=True)
    
    def get_wi_backup(self, wi_id):
        """
        Takes in a WI ID string and returns None if no backup of the WI exists,
        or a work item object that was backed up during the previous poll.
        """
        key = self.wi_backup_key_fmt + str(wi_id)
        return storage_obj_read(key, lock=True)

    def set_wi_backup(self, wi):
        """
        Takes in a work item object and writes it out to disk.
        """
        key = self.wi_backup_key_fmt + str(wi.id)
        storage_obj_write(key, wi, lock=True)

    def poll_action(self):
        """
        Implementation of the abstract poll() function.
        """
        # get the specified teams
        config_teams = self.config.get("teams")
        self.teams = []
        if config_teams is None:
            self.teams = ado_project_get_teams(self.project)
        else:
            for t in config_teams:
                self.teams.append(ado_find_team(self.project, t))
        self.dbg_print("Retrieved %d teams." % len(self.teams))

        # load the specified work items
        self.wis = []
        config_wis = self.config.get("work_items")
        if config_wis is None:
            for team in self.teams:
                try:
                    wis = ado_team_get_workitems(self.project, team)
                    self.wis += wis
                    self.dbg_print("Retrieved %d work items from team \"%s%s%s\"." %
                                   (len(wis), color("team"), team.name, color("none")))
                except:
                    self.dbg_print("Failed to retrieve work items from team \"%s%s%s\"." %
                                   (color("team"), team.name, color("none")))
        else:
            self.wis = ado_project_get_workitems_by_id(config_wis)
        self.dbg_print("Finished retrieving %d work items." % len(self.wis))
        
        # for each work item, attempt to read a previous version from disk
        self.wis_backups = {}
        for wi in self.wis:
            wi_old = self.get_wi_backup(wi)
            if wi_old is not None:
                self.wis_backups[wi_old.id] = wi_old

        # this is an intermediate implementation - the subclasses will
        # carry on from this point (return None)
        return None

    def cleanup_action(self):
        """
        Overridden cleanup_action().
        """
        # write all loaded work items out to disk
        for wi in self.wis:
            self.set_wi_backup(wi)


# ============================= WI Changed State ============================= #
class EventConfig_WI_State_Changed(EventConfig_WI):
    """
    An extension of the EventConfig_WI class specific for changing a WI's state.
    """

class Event_WI_State_Changed(Event_WI):
    """
    An extension of the Event_WI class specific for changing a WI's state.
    """
    def cmp_wi(self, wi_new, wi_old):
        """
        Compares a work item's current and former self, and returns either:
         - True or False
         - None or non-None data
        """
        state_new = wi_new.fields["System.State"]
        state_old = wi_old.fields["System.State"]
        self.dbg_print("WI-%s state: old=\"%s\", new=\"%s\"" %
                       (wi_new.id, state_old, state_new))
        
        if state_new.strip().lower() != state_old.strip().lower():
            return state_new
        return None

    def poll_action(self):
        """
        Overridden poll_action().
        """
        super().poll_action()

        # iterate through each work item
        results = []
        for wi in self.wis:
            # if a backup doesn't exist for this work item, we can't yet detect
            # if this event has occurred
            wi_old = self.get_wi_backup(wi.id)
            if wi_old is None:
                continue

            r = self.cmp_wi(wi, wi_old)
            if r is True:
                results.append(self.package_result(wi))
            elif r not in [False, None]:
                results.append(self.package_result(wi, culprits=r))

        results_len = len(results)
        self.dbg_print("Found %s WI(s) with changed states." %
                       ("no" if results_len == 0 else str(results_len)))
        return None if results_len == 0 else results

# ============================ WI Gained Comment ============================= #
class EventConfig_WI_Comment_New(EventConfig_WI_State_Changed):
    """
    An extension of the EventConfig_WI class specific for adding a new WI comment.
    """

class Event_WI_Comment_New(Event_WI_State_Changed):
    """
    An extension of the Event_WI class specific for adding a new WI comment.
    """
    def cmp_wi(self, wi_new, wi_old):
        """
        Compares a work item's current and former self, and returns either:
         - True or False
         - None or non-None data
        """
        cnt_new = wi_new.fields["System.CommentCount"]
        cnt_old = wi_old.fields["System.CommentCount"]
        self.dbg_print("WI-%s comment count: old=%d, new=%d" %
                       (wi_new.id, cnt_old, cnt_new))
        return cnt_new > cnt_old

