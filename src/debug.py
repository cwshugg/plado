# This module defines debugging helper functions for fancy debug prints.
# A series of flags are used to determine what debug messages can be printed.

# Imports
import os
import sys
import threading

# Path setup
srcdir = os.path.realpath(os.path.dirname(__file__))
if srcdir not in sys.path:
    sys.path.append(srcdir)

# Tool imports
from env import env
from utils.colors import color

dbg_flags = {
    "config": False,                        # config file debugging
    "ado": False,                           # ADO debugging
    "event": False,                         # event monitoring
    "event_pr_create": False,               # event monitoring for pr_create
    "event_pr_draft_on": False,             # event monitoring for pr_draft_on
    "event_pr_draft_off": False,            # event monitoring for pr_draft_off
    "event_pr_commit_new_src": False,       # event monitoring for pr_commit_new_src
    "event_pr_commit_new_dst": False,       # event monitoring for pr_commit_new_dst
    "event_pr_status_change": False,        # event monitoring for pr_status_change
    "event_pr_reviewer_added": False,       # event monitoring for pr_reviewer_added
    "event_pr_reviewer_voted": False,       # event monitoring for pr_reviewer_voted
    "event_pr_comment_added": False,        # event monitoring for pr_comment_added
    "event_pr_comment_edited": False,       # event monitoring for pr_comment_edited
    "event_pr_comment_liked": False,        # event monitoring for pr_comment_liked
    "event_pr_comment_unliked": False,      # event monitoring for pr_comment_unliked
    "event_pr_comment_resolved": False,     # event monitoring for pr_comment_resolved
    "event_pr_comment_unresolved": False,   # event monitoring for pr_comment_unresolved
    "event_branch_commit_new": False,       # event monitoring for branch_commit_new
}

def dbg_set(flag: str, enabled: bool):
    """
    Sets a debug flag to be enabled (True) or disabled (False).
    """
    if flag not in dbg_flags:
        raise Exception("Debug Error: Unrecognized debug flag: \"%s\"." % flag)
    dbg_flags[flag] = enabled

def dbg_init():
    """
    Checks environment variables and toggles flags accordingly.
    """
    for flag in dbg_flags:
        if env("DEBUG_%s" % flag.upper()) == True:
            dbg_set(flag, True)
            dbg_print(flag, "Debug printing enabled.")

def dbg_print(context: str, msg: str, end="\n"):
    """
    Prints to stderr and requires that a "context" (a flag name) be given. If
    the flag is enabled, the print occurs. If not, the print is ignored.
    """
    if context not in dbg_flags:
        raise Exception("Debug Error: Unrecognized debug flag: \"%s\"." % context)
    if not dbg_flags[context]:
        return

    # determine if we're in the main thread or not
    mt = threading.main_thread().native_id
    ct = threading.current_thread().native_id
    thread_str = ""
    if ct != mt:
        thread_str = " T-%s%s%s" % (color(str(ct)), ct, color("none"))
    
    # create a prefix to print with, based on the context
    context_color = color(context)
    pfx = "%s[%sdebug%s.%s%s%s%s%s]%s " % \
          (color("dkgray"), color("dbg"), color("dkgray"),
           context_color, context, color("none"),
           thread_str, color("dkgray"), color("none"))

    # print to stderr
    sys.stderr.write("%s%s%s" % (pfx, msg, end))

