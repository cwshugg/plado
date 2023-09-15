# This module implements various helper functions for different prints for
# command-line tools.
#
#   Connor Shugg

# Imports
import os
import sys
import traceback

# Library path setup
srcdir = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))
if srcdir not in sys.path:
    sys.path.append(srcdir)

# Library imports
from utils.colors import *

# ADO imports
from azure.devops.exceptions import AzureDevOpsServiceError

# Globals
bullet_char = "•"


# ============================== Error Handling ============================== #
def panic(msg: str, exception=None, exit=True):
    """
    Writes a message to stderr, prefixed to indicate a fatal error, then exits.
    If an exception is given, the message and stacktrace is printed.
    """
    pfx = "%s!%s" % (color("red"), color("none"))
    sys.stderr.write("%s %s\n" % (pfx, msg))
    if exception is not None:
        # if the exception is an Azure DevOps Serivce Error, we'll treat it
        # differently here
        if type(exception) == AzureDevOpsServiceError:
            sys.stderr.write("%s Azure DevOps says: \"%s\"\n" % (pfx, exception))
        else:
            # get the traceback and print each line
            tb = traceback.format_exc()
            for line in tb.split("\n"):
                if len(line) > 0:
                    sys.stderr.write("%s %s%s%s\n" % (pfx, color("gray"), line, color("none")))
    if exit:
        sys.exit(1)


# ================================= Printing ================================= #
def eprint(msg: str, end="\n"):
    """
    Writes a message to stderr, prefixed to indicate an error.
    """
    pfx = "%s?%s" % (color("yellow"), color("none"))
    sys.stderr.write("%s %s%s" % (pfx, msg, end))

def dprint(msg: str, end="\n"):
    """
    Writes a message to stderr.
    Useful for debug/diagnostic messages you don't want picked up in stdout.
    """
    sys.stderr.write("%s%s" % (msg, end))


# =========================== String Manipulation ============================ #
def str_tab(count=1, bullet=None, bullet_color=None):
    """
    Returns a string representing a number of indents/tabs. (Default is 1).
    If a 'bullet' is given, it will be inserted into the string-tab as a bullet
    in a bulleted list.
    """
    if bullet is not None:
        assert len(bullet) >= 1
        c1 = color("dkgray") if bullet_color is None else bullet_color
        c2 = color("none")
        return ("    " * (count - 1)) + ("  %s%s%s " % (c1, bullet, c2))
    return "    " * count

def str_file_size(size: int):
    """
    Takes in a file size and returns a human-readable representation of the
    size.
    """
    sizes = [
        {"name": "GB", "size": 1000000000},
        {"name": "MB", "size": 1000000},
        {"name": "KB", "size": 1000},
    ]
    for s in sizes:
        if size >= s["size"]:
            return "%.2f %s" % (float(size) / s["size"], s["name"])
    return "%d B" % size


# ============================= JSON Operations ============================== #
def json_try_get(jdata: dict, keychain, default=None):
    """
    Returns 'default' if the field doesn't exist, otherwise returns the actual
    value found in the dictionary. The 'keychain' is a list of keys (or a single
    key) that represents the hierarchy of keys to look for in the given JSON
    object. For example, if `keychain = ["info", "name"]`, then this code would
    look for `jdata["info"]["name"]`.
    """
    if type(keychain) == str:
        keychain = [keychain]

    j = jdata
    # walk down the chain of keys looking for the entry
    for key in keychain:
        # if the key isn't present, return the default
        if key not in j:
            return default
        j = j[key]
    # return the found value
    return j

