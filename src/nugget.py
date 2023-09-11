# This funnily-named module provides a simple interface for reading and writing
# metadata to individual files ("nuggets of knowledge"). Any part of this
# program may choose to write to (or read from) a "nugget" at any time.
#
# Nuggets are tied to the location of the config file specified by the user.
# If the path of a config file is changed, or a different config file is used,
# previously-written nuggets will not be used during execution.

# Imports
import os
import sys

# Library path setup
srcdir = os.path.realpath(os.path.dirname(__file__))
if srcdir not in sys.path:
    sys.path.append(srcdir)

# Tool imports
from config import *
from debug import dbg_print
from utils.utils import *

class Nugget:
    """
    Represents a single nugget, which is a small file containing a single piece
    of metadata.
    """
    def __init__(self, name: str, types: list):
        """
        Constructor. Takes in a name, which is directly used to determine the
        name of the nugget file. Also takes in a list of accepted types for the
        data written in the nugget.
        """
        self.name = name
        self.types = types

    def path(self):
        """
        Uses the nugget's name and the location of the global config file to
        form a file path at which the nugget should be located.
        """
        config = config_load()
        if config.path is None:
            panic("The global config does not have a file path. This should not happen.")
        
        config_dir = os.path.dirname(config.path)
        config_file = os.path.basename(config.path)
        nugget_file = ".%s.%s.nugget" % \
                      (config_file, self.name)
        path = os.path.join(config_dir, nugget_file)
        return path

    def write(self, value):
        """
        Takes in a value and writes it to the nugget file.
        """
        # make sure the type is correct
        if type(value) not in self.types:
            panic("The given value for nugget \"%s\" must be one of the "
                  "following types: %s" % (self.name, str(self.types)))

        # write to the file
        path = self.path()
        with open(path, "w") as fp:
            fp.write(str(value))

    def read(self):
        """
        Looks for a nugget file and attempts to read its value.
        If the file cannot be found or is empty, None is returned.
        Otherwise, the string read from the file is checked against the nugget's
        accepted types, and the value is returned as the first-matching type.
        """
        path = self.path()
        if not os.path.isfile(path):
            return None

        with open(path, "r") as fp:
            value = fp.read()
            # if reading resulting in NOTHING, the file must be empty
            if value is None or len(value) == 0:
                return None

            # attempt to convert to all accepted types, one at a time
            for t in self.types:
                try:
                    return t(value)
                except:
                    continue
            # if ALL fail, panic
            panic("The text stored in nugget \"%s\" could not be converted to "
                  "one of the following types: %s" % (self.name, str(self.types)))

