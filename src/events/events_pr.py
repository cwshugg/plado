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
        """
        Overridden poll_action().
        """
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
        self.dbg_print("Found %s new PRs." %
                       ("no" if new_prs_len == 0 else str(new_prs_len)))
        return None if new_prs_len == 0 else new_prs


# ========================= PR Draft Enable/Disable ========================== #
class EventConfig_PR_Draft_On(EventConfig_PR):
    """
    An extension of the EventConfig_PR class specific for a PR's draft mode
    being enabled.
    """
    def __init__(self):
        super().__init__()
        self.fields.update({
            "include_new_pullreqs": ConfigField(
                "include_new_pullreqs",
                [bool],
                description="Set to true to have this event trigger for new "
                            "Pull Requests created with the desired draft mode.",
                required=False,
                default=False
            )
        })


class Event_PR_Draft_On(Event_PR):
    """
    An extension of the Event_PR class specific for a PR's draft mode being
    enabled.
    """
    def __init__(self, conf: EventConfig_PR_Draft_On):
        """
        Constructor.
        """
        super().__init__(conf)
        self.desired_state = True # meaning, we want to see draft mode ON

    def poll_action(self):
        """
        Overridden poll_action().
        """
        super().poll_action()
        # if we don't have a backup of PR data from a previous poll, we can't
        # yet detect if this event has happened
        if self.pr_backups is None:
            return None

        # for each pull request currently active
        results = []
        for pr in self.prs:
            # if the PR was *just* created, add it to the results if it was
            # created in draft mode and the correct config option is set
            if pr.code_review_id not in self.pr_backups:
                if pr.is_draft == self.desired_state and \
                   self.config.get("include_new_pullreqs"):
                    results.append(pr.as_dict())
                continue

            # otherwise, grab the old copy of the PR and compare the draft mode
            # to see if it went from OFF --> ON
            pr_old = self.pr_backups[pr.code_review_id]
            if pr_old.is_draft != self.desired_state and \
               pr.is_draft == self.desired_state:
                results.append(pr.as_dict())
                       
        results_len = len(results)
        self.dbg_print("Found %s PRs that were recently switched to draft mode." %
                       ("no" if results_len == 0 else str(results_len)))
        return None if results_len == 0 else results

class EventConfig_PR_Draft_Off(EventConfig_PR_Draft_On):
    """
    An extension of the EventConfig_PR class specific for a PR's draft mode
    being disabled.
    """

class Event_PR_Draft_Off(Event_PR_Draft_On):
    """
    An extension of the Event_PR class specific for a PR's draft mode being
    disabled.
    """
    def __init__(self, conf: EventConfig_PR_Draft_Off):
        """
        Constructor.
        """
        super().__init__(conf)
        self.desired_state = False # meaning, we want to see draft mode OFF


# ================================ PR Commits ================================ #
class EventConfig_PR_Commit_New_Src(EventConfig_PR):
    """
    An extension of the EventConfig_PR class specific for a PR receiving a new
    commit from the source branch.
    """

class Event_PR_Commit_New_Src(Event_PR):
    """
    An extension of the Event_PR class specific for a PR receiving a new
    commit from the source branch.
    """
    def __init__(self, conf: EventConfig_PR_Commit_New_Src):
        """
        Constructor.
        """
        super().__init__(conf)
        self.src = True # meaning, we want to check src branch for
                        # a new commit

    def poll_action(self):
        """
        Overridden poll_action().
        """
        super().poll_action()
        # if we don't have a backup of PR data from a previous poll, we can't
        # yet detect if this event has happened
        if self.pr_backups is None:
            return None

        # for each pull request currently active
        results = []
        for pr in self.prs:
            # ignore new PRs
            if pr.code_review_id not in self.pr_backups:
                continue
            pr_old = self.pr_backups[pr.code_review_id]
            
            # otherwise, examine the commit hash of the latest commit for the
            # desired branch
            commit_new = pr.last_merge_source_commit if self.src else \
                         pr.last_merge_target_commit
            commit_old = pr_old.last_merge_source_commit if self.src else \
                         pr_old.last_merge_target_commit
            
            # compare the commits; if the new is different from the old, then
            # add it to the result list
            self.dbg_print("PR-%s previous %s commit hash: %s" %
                           (str(pr.code_review_id),
                            "source" if self.src else "target",
                            commit_old.commit_id))
            self.dbg_print("PR-%s latest %s commit hash:   %s" %
                           (str(pr.code_review_id),
                            "source" if self.src else "target",
                            commit_new.commit_id))
            if commit_new.commit_id != commit_old.commit_id:
                self.dbg_print("PR-%s has a new %s commit!" %
                               (str(pr.code_review_id),
                                "source" if self.src else "target"))
                results.append(pr.as_dict())

        results_len = len(results)
        self.dbg_print("Found %s PRs that recently received new commits." %
                       ("no" if results_len == 0 else str(results_len)))
        return None if results_len == 0 else results

class EventConfig_PR_Commit_New_Dst(EventConfig_PR_Commit_New_Src):
    """
    An extension of the EventConfig_PR class specific for a PR receiving a new
    commit from the target (destination) branch.
    """

class Event_PR_Commit_New_Dst(Event_PR_Commit_New_Src):
    """
    An extension of the Event_PR class specific for a PR receiving a new
    commit from the target (destination) branch.
    """
    def __init__(self, conf: EventConfig_PR_Commit_New_Dst):
        """
        Constructor.
        """
        super().__init__(conf)
        self.src = False # meaning, we want to check dst branch for
                         # a new commit


# ============================= PR Status Change ============================= #
class EventConfig_PR_Status_Change(EventConfig_PR):
    """
    An extension of the EventConfig_PR class specific for a PR's status being
    changed.
    """
    def __init__(self):
        super().__init__()
        self.fields.update({
            "desired_status": ConfigField(
                "desired_status",
                [str],
                description="Set to be the status you want this event to trigger "
                            "on. If not specified, all status changes will "
                            "trigger the event.",
                required=False,
                default=None
            )
        })

class Event_PR_Status_Change(Event_PR):
    """
    An extension of the Event_PR class specific for a PR's status being changed.
    """
    def poll_action(self):
        """
        Overridden poll_action().
        """
        super().poll_action()
        # if we don't have a backup of PR data from a previous poll, we can't
        # yet detect if this event has happened
        if self.pr_backups is None:
            return None

        # for each pull request currently active
        results = []
        for pr in self.prs:
            # ignore new PRs
            if pr.code_review_id not in self.pr_backups:
                continue
            pr_old = self.pr_backups[pr.code_review_id]
            
            # otherwise, examine the old and new statuses
            status_new = pr.status
            status_old = pr_old.status
            self.dbg_print("PR-%s status: old=\"%s\", new=\"%s\"." %
                           (pr.code_review_id, status_new, status_old))

            # if they don't match, there's been a change
            if status_new != status_old:
                # if a desired status is specified, check for this too
                ds = self.config.get("desired_status")
                if ds is not None and \
                   status_new.strip().lower() == ds.strip().lower():
                    self.dbg_print("PR-%s's new status matches the desired status." %
                                   pr.code_review_id)
                    result.append(pr.as_dict())
                else:
                    self.dbg_print("PR-%s's status has changed." %
                                   pr.code_review_id)
                    result.append(pr.as_dict())
                       
        results_len = len(results)
        self.dbg_print("Found %s PRs that changed status." %
                       ("no" if results_len == 0 else str(results_len)))
        return None if results_len == 0 else results


# ============================ PR Reviewer Added ============================= #
class EventConfig_PR_Reviewer_Added(EventConfig_PR):
    """
    An extension of the EventConfig_PR class specific for adding a PR reviewer.
    """
    def __init__(self):
        super().__init__()
        self.fields.update({
            "user": ConfigField(
                "user",
                [str],
                description="Name, email, or username of the desired user to track.",
                required=False,
                default=None
            ),
            "only_optional": ConfigField(
                "only_optional",
                [bool],
                description="Set to true to only trigger when a/the reviewer is optional.",
                required=False,
                default=False
            ),
            "only_required": ConfigField(
                "only_required",
                [bool],
                description="Set to true to only trigger when a/the reviewer is required.",
                required=False,
                default=False
            ),
        })

class Event_PR_Reviewer_Added(Event_PR):
    """
    An extension of the Event_PR class specific for adding a PR reviewer.
    """
    def match_reviewer_name(self, rev):
        """
        Returns True if the configured 'user' field matches the given reviewer.
        """
        user = self.config.get("user")
        if user is None:
            return True

        unique_name = rev.unique_name.lower().strip()
        user = user.strip().lower()

        # extract the username from an email address (if possible)
        user_email_name = unique_name if "@" not in unique_name else \
                            unique_name.split("@")[0]
        
        # compare against the display name, unique name, and extracted name
        match = rev.display_name.lower().strip() == user or \
                unique_name == user or \
                user_email_name == user
        return match

    def check_reviewers(self, pr, revs_new: dict, revs_old: dict):
        """
        Performs checks on the PR reviewers, given the new and old list.
        Subclasses will define their own to implement other reviewer-related
        events.
        """
        # iterate over the lists
        for name in revs_new:
            # if a new reviewer is spotted...
            if name not in revs_old:
                rev = revs_new[name]
                is_required = hasattr(rev, "is_required") and rev.is_required

                self.dbg_print("PR-%s: New reviewer \"%s\" is %srequired." %
                               (str(pr.code_review_id), rev.unique_name,
                                "NOT " if not is_required else ""))

                # check for for required or optional, depending on the config
                if self.config.get("only_optional") and is_required:
                    continue
                if self.config.get("only_required") and not is_required:
                    continue

                # check for a matching user, if configured
                if not self.match_reviewer_name(rev):
                    continue

                self.dbg_print("PR-%s: Found new %s valid reviewer: \"%s\"." %
                               (str(pr.code_review_id),
                                "required" if is_required else "optional",
                                rev.unique_name))

                # return True to tell poll_action() to add this PR to the
                # result list
                return True
        
        # if we reached the bottom before returning True, then there must be no
        # new matching reviewers
        return False

    def poll_action(self):
        """
        Overridden poll_action().
        """
        super().poll_action()
        # if we don't have a backup of PR data from a previous poll, we can't
        # yet detect if this event has happened
        if self.pr_backups is None:
            return None

        # for each pull request currently active
        results = []
        for pr in self.prs:
            # ignore new PRs
            if pr.code_review_id not in self.pr_backups:
                continue
            pr_old = self.pr_backups[pr.code_review_id]

            # grab both list of reviewers and convert to dictionaries, indexed by
            # unique reviewer name
            revs_new = {}
            for rev in pr.reviewers:
                revs_new[rev.unique_name] = rev
            revs_old = {}
            for rev in pr_old.reviewers:
                revs_old[rev.unique_name] = rev
            
            # if the checks pass, add this PR to the list
            if self.check_reviewers(pr, revs_new, revs_old):
                results.append(pr.as_dict())
            
        results_len = len(results)
        self.dbg_print("Found %s PRs with reviewer updates." %
                       ("no" if results_len == 0 else str(results_len)))
        return None if results_len == 0 else results


# ============================ PR Reviewer Voted ============================= #
class EventConfig_PR_Reviewer_Voted(EventConfig_PR_Reviewer_Added):
    """
    An extension of the EventConfig_PR class specific for a PR reviewer voting.
    """
    def __init__(self):
        super().__init__()
        self.fields.update({
            "desired_vote": ConfigField(
                "desired_vote",
                [int],
                description="The specific integer value of the reviewer's vote you"
                            "want this event to trigger for.",
                required=False,
                default=None
            ),
        })

class Event_PR_Reviewer_Voted(Event_PR_Reviewer_Added):
    """
    An extension of the Event_PR class specific for adding a PR reviewer.
    """
    def check_reviewers(self, pr, revs_new: dict, revs_old: dict):
        """
        Performs checks on the PR reviewers, given the new and old list.
        Subclasses will define their own to implement other reviewer-related
        events.
        """
        # iterate over the lists
        for name in revs_new:
            # skip new reviewers
            if name not in revs_old:
                continue
            rev = revs_new[name]

            # get the reviewer's previous and current vote
            vote_new = revs_new[name].vote
            vote_old = revs_old[name].vote
            self.dbg_print("PR-%s: Reviewer \"%s\" vote: old=%s%s%s, new=%s%s%s." %
                           (str(pr.code_review_id), name,
                            color(str(vote_old)), str(vote_old), color("none"),
                            color(str(vote_new)), str(vote_new), color("none")))

            # if the vote values match, then nothing has changed
            if vote_new == vote_old:
                continue

            # look at the configured 'only_*' fields and skip if this reviewer
            # doesn't apply
            is_required = hasattr(rev, "is_required") and rev.is_required
            if self.config.get("only_optional") and is_required:
                continue
            if self.config.get("only_required") and not is_required:
                continue
            
            # make sure the configured username matches
            if not self.match_reviewer_name(rev):
                continue

            # if the vote value (if given) doesn't match, skip this one
            desired_vote = self.config.get("desired_vote")
            if desired_vote is not None and vote_new != desired_vote:
                continue
            
            # all checks passed: return True
            self.dbg_print("PR-%s: Reviewer \"%s\" has a valid/matching vote." %
                           (str(pr.code_review_id), name))
            return True

        return False

