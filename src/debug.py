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
    "config": False,    # config file debugging
    "ado": False,       # ADO debugging
    "event": False      # event monitoring
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
    if env("DEBUG_CONFIG") == True:
        dbg_set("config", True)
        dbg_print("config", "Debug printing enabled.")
    if env("DEBUG_ADO") == True:
        dbg_set("ado", True)
        dbg_print("ado", "Debug printing enabled.")
    if env("DEBUG_EVENT") == True:
        dbg_set("event", True)
        dbg_print("event", "Debug printing enabled.")

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



