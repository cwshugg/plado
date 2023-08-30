# This module implements configuration settings for the tool. It can parse JSON
# files and data and does some basic type-checking while parsing. This config
# object is intended to be used as the single source of truth for user-supplied
# information at runtime.

# Imports
import os
import sys
import json

# Path setup
srcdir = os.path.realpath(os.path.dirname(__file__))
if srcdir not in sys.path:
    sys.path.append(srcdir)

# Tool imports
from debug import dbg_print

# Globals
conf = None # global config reference


# ============================== Config Fields =============================== #
class ConfigField:
    """
    A class that represents a single config field entry. It has a name, a list
    of acceptable types, whether or not the field is required in the config, and
    a default value (which is used if the field isn't required).
    """
    def __init__(self, name, types, description="", required=False, default=None):
        """
        Constructor. Accepts the name, the acceptable types, and optional
        parameters regarding requirement and default.
        """
        self.name = name            # name of the field
        self.description = description # description of field
        self.types = types          # allowed types for the field
        self.required = required    # whether or not the field is required
        self.default = default      # default value for non-required fields
        self.value = default        # current value of the field

    def type_match(self, value: any):
        """
        Checks the given type against the field's acceptable types.
        Returns True if there is a match, and False otherwise.
        """
        return type(value) in self.types

    def set(self, value: any):
        """
        Checks the given new value against the allowed types and updates the
        field. If the type isn't allowed an exception is thrown.
        """
        # check the type and throw an exception if necessary
        if type(value) not in self.types:
            raise Exception("ConfigField Error: Field \"%s\" must be one of "
                            "the following types: %s" %
                            (self.name, str(self.types)))
        # update the value
        self.value = value
        dbg_print("config", "Set field \"%s\" to: %s." % (self.name, str(value)))

    def get(self):
        """
        Returns the field's value.
        """
        return self.value


# ============================ Main Config Class ============================= #
# Config class.
class Config:
    def __init__(self):
        """
        Constructor. Creates the config object.
        """
        self.fields = {
            "ado_pat": ConfigField(
                "ado_pat",
                [str],
                description="Your Azure DevOps Personal Access Token",
                required=True
            ),
            "ado_org": ConfigField(
                "ado_org",
                [str],
                description="Your Azure DevOps Organization Name OR full URL "
                            "(ex: \"ORG_NAME\" or \"https://dev.azure.com/ORG_NAME\")",
                required=True
            )
        }
    
    def __str__(self):
        """
        Creates and returns a string representation, in JSON, of the config and
        all of its fields.
        """
        jdata = self.to_json()
        return json.dumps(jdata, indent=4)
    
    # ---------------------------- Field Get Set ----------------------------- #
    def get(self, name: str):
        """
        Searches the config for a field with the given name. If the field name
        is not recognized, an exception is thrown. Otherwise, the field's value
        is returned.
        """
        if name in self.fields:
            return self.fields[name].get()
        raise Exception("Config Error: Unrecognized field name: \"%s\"" % name)

    def set(self, name: str, value: any):
        """
        Takes in a config field name and a value and attempts to update the
        field's value. If the field name is not recognized, an exception is
        thrown. If the type of the new value is not appropriate for the field,
        it will an exception will be thrown.
        """
        if name in self.fields:
            self.fields[name].set(value)
            return
        raise Exception("Config Error: Unrecognized field name: \"%s\"" % name)
    
    # --------------------------- Initial Parsing ---------------------------- #
    def parse_file(self, fpath: str):
        """
        Takes in a file path and reads in the contents. The contents are
        expected to be in JSON format. All defined fields are searched for in
        the JSON, and initialized if found.
        """
        dbg_print("config", "Attempting to read JSON from file: %s" % fpath)
        # open the file for reading, and parse as JSON
        fp = open(fpath, "r")
        jdata = json.load(fp)
        fp.close()
        
        # invoke the JSON-parsing function
        self.parse_json(jdata)

    def parse_json(self, jdata: dict):
        """
        Takes in a dictionary (JSON data) and attempts to parse all the config
        fields defined in the class.
        """
        for name in self.fields:
            f = self.fields[name]

            # if the name is present in the JSON data, attempt to set
            if f.name in jdata:
                self.set(f.name, jdata[name])
                continue
            
            # if it's required but not found, complain
            if f.required:
                raise Exception("Config Error: Required field \"%s\" not found." % f.name)
            
            # otherwise, set the value to the field's default
            self.set(f.name, f.default)
    
    # ------------------------------- Helpers -------------------------------- #
    # Converts the config into a JSON dictionary and returns it.
    def to_json(self):
        result = {}
        # convert all expected fields to JSON
        for key in self.fields:
            f = self.fields[key]
            result[f.name] = f.get()
        return result


# ============================== Global Access =============================== #
def config_store(c: Config):
    """
    Takes in a Config object and stores a reference to it in the global variable
    defined in this module.
    """
    global conf
    conf = c

def config_load():
    """
    Returns the global config reference.
    """
    global conf
    return conf

