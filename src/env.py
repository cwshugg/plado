# This module implements a collection of environment variables for use by
# the rest of the program.

# Imports
import os
import abc


# ================================ Base Class ================================ #
class EnvironmentVariable(abc.ABC):
    """
    A class that represents an interface around an environment variable.
    This class serves as an abstract base class for the enviornment variables
    to extend and implement their own parsing functions.
    """
    def __init__(self, name: str, description=""):
        """
        Constructor. Takes in the name and other optional parameters.
        """
        self.name = name
        self.description = description
    
    @abc.abstractmethod
    def load(self):
        """
        Abstract method that loads the environment variable's string value and
        attempts to parse it according. This must be implemented by child
        classes.
        This function must return the loaded environment value. If the given
        value causes some parsing error, an exception must be thrown.
        """
        pass


# =============================== Sub-Classes ================================ #
class EnvironmentVariable_String(EnvironmentVariable):
    """
    An environment variable whose expected type is a string.
    """
    def load(self):
        if self.name not in os.environ:
            return None
        return str(os.environ[self.name])

class EnvironmentVariable_Bool(EnvironmentVariable):
    """
    An environment variable whose expected type is a boolean.
    Returns None if the variable wasn't found.
    Returns False if the variable is "0", "false", or "no"
    Returns True if the variable is any other string.
    """
    def load(self):
        if self.name not in os.environ:
            return None
        val = str(os.environ[self.name]).strip().lower()

        # check for false before assuming true
        if val in ["0", "false", "no"]:
            return False
        return True


# ================================ Interface ================================= #
env_prefix = "PLADO_"
env_vars = {
    env_prefix + "CONFIG": EnvironmentVariable_String(
        env_prefix + "CONFIG",
        description="A path to your JSON config file. Overridden by --config."
    ),
    # DEBUGGING ENVIRONMENT VARIABLES
    env_prefix + "DEBUG_CONFIG": EnvironmentVariable_Bool(
        env_prefix + "DEBUG_CONFIG",
        description="Set to 1 to enable debug prints for configuration file code."
    ),
    env_prefix + "DEBUG_ADO": EnvironmentVariable_Bool(
        env_prefix + "DEBUG_ADO",
        description="Set to 1 to enable debug prints for Azure DevOps interaction code."
    ),
    env_prefix + "DEBUG_EVENT": EnvironmentVariable_Bool(
        env_prefix + "DEBUG_EVENT",
        description="Set to 1 to enable debug prints for event monitoring code."
    )
}
# add event-specific debug variables
enames = [
    "pr_create",
    "pr_draft_on",
    "pr_draft_off",
    "pr_commit_new_src",
    "pr_commit_new_dst",
    "pr_status_change",
    "pr_reviewer_added",
    "pr_reviewer_voted",
    "pr_comment_added",
    "pr_comment_edited",
    "pr_comment_liked",
    "pr_comment_unliked",
    "pr_comment_resolved",
    "pr_comment_unresolved",
    "branch_commit_new",
]
for ename in enames:
    name = "DEBUG_EVENT_%s" % ename.upper()
    env_vars[env_prefix + name] = EnvironmentVariable_Bool(
        env_prefix + name,
        description="Set to 1 to enable debug prints for %s event monitoring." % ename
    )

def env_init():
    """
    Initializes environment variable interface and attempts to load in all
    program-defined environment variables.
    """
    for key in env_vars:
        ev = env_vars[key]
        ev.load()

def env(name: str):
    """
    Looks for the presence of the given environment variable and returns the
    value. If the variable name (when prefixed with 'PLADO_') is one of the
    program-specific environment variables, the value returned will depend on
    the expected type of the variable.
    Otherwise, the non-prefixed name is searched for in the system-wide
    list of environment variables, and the value (if one is found), is returned
    as a string.
    """
    pfx_name = env_prefix + name
    if pfx_name in env_vars:
        return env_vars[pfx_name].load()
    # if the name isn't in the known, program-defined list, interpret as a
    # string-typed environment variable and attempt to load it
    return EnvironmentVariable_String(name).load()

