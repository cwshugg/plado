# This module defines event config objects, extended from the base Config
# object defined in config.py.

# Imports
import os
import sys

# Library path setup
srcdir = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))
if srcdir not in sys.path:
    sys.path.append(srcdir)

# Tool imports
from config import Config, ConfigField


class EventJobConfig(Config):
    """
    A class that defines a job to run when an event is fired.
    """
    def __init__(self):
        """
        Constructor for the event job configuration.
        """
        self.fields = {
            "args": ConfigField(
                "args",
                [list],
                description="Command-line arguments to run the job.",
                required=True
            ),
            "name": ConfigField(
                "name",
                [str],
                description="An optional nickname to give the job.",
                required=False,
                default=None
            ),
            "run_dir": ConfigField(
                "run_dir",
                [str],
                description="A path to the directory from which this job "
                            "should be run.",
                required=False,
                default=None
            ),
            "timeout": ConfigField(
                "timeout",
                [str],
                description="The number of seconds the job is allowed to run "
                            "before it is killed.",
                required=False,
                default=120
            )
        }

class EventConfig(Config):
    """
    A class that defines configuration fields for a single event to be monitored
    by the program. These events are to be defined in the main configuration
    file.
    """
    def __init__(self):
        """
        Constructor for the event configuration.
        """
        self.fields = {
            "type": ConfigField(
                "type",
                [str],
                description="The name of the type of event you wish to monitor.",
                required=True
            ),
            "jobs": ConfigField(
                "jobs",
                [list],
                description="A list containing lists of command-line arguments, "
                            "representing tasks to be executed when the event"
                            "occurs.",
                required=True
            ),
            "name": ConfigField(
                "name",
                [str],
                description="An optional nickname to give the event.",
                required=False,
                default=None
            ),
        }

