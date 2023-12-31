#!/usr/bin/env python3
# The main source file for this tool.

# Imports
import os
import sys
import stat
import argparse
import getpass
import json
import shutil

# Library path setup
srcdir = os.path.realpath(os.path.dirname(__file__))
if srcdir not in sys.path:
    sys.path.append(srcdir)

# Tool imports
from config import *
from env import env_init, env, env_vars
from debug import dbg_init, dbg_print
from ado import *
from event_monitoring import *
from utils.colors import *
from utils.utils import *

# Globals
config_path_default = os.path.expandvars("${HOME}/.plado_config.json")
args = None


# ============================= Argument Parsing ============================= #
def args_init():
    """
    Creates and initializes the command-line argument parser.
    """
    desc = "Interact with Azure DevOps on the command-line and monitor for events."
    p = argparse.ArgumentParser(description=desc,
                                argument_default=None,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    # program-specific arguments
    p.add_argument("-c", "--config",
                   help="Sets the path to the JSON config to read as input.",
                   type=str, default=None, required=True, metavar="CONFIG_JSON")
    p.add_argument("--color",
                   help="Enables/disables color printing. (Default: enabled when printing to terminal)",
                   type=str, default=None, required=False, metavar="on/off")

    # ADO configuration arguments
    p.add_argument("-p", "--project",
                   help="Sets the ADO project to interact with. Can be a name or ID.",
                   type=str, default=None, required=False, metavar="PROJ_NAME_OR_ID")
    p.add_argument("-r", "--repo",
                   help="Sets the ADO project repository to interact with. Can be a name or ID.",
                   type=str, default=None, required=False, metavar="REPO_NAME_OR_ID")
    p.add_argument("-b", "--branch",
                   help="Sets the ADO repository branch to interact with.",
                   type=str, default=None, required=False, metavar="REPO_NAME_OR_ID")
    p.add_argument("-t", "--team",
                   help="Sets the ADO team to interact with.",
                   type=str, default=None, required=False, metavar="TEAM_NAME_OR_ID")
    p.add_argument("-B", "--backlog",
                   help="Sets the ADO backlog to interact with.",
                   type=str, default=None, required=False, metavar="BACKLOG_NAME_OR_ID")

    # monitor mode arguments
    p.add_argument("-m", "--monitor",
                   help="Enables event monitoring daemon mode.",
                   default=False, action="store_true")
    
    # ADO routine arguments
    p.add_argument("--show-projects",
                   help="Lists all projects within the configured organization.",
                   default=False, action="store_true")
    p.add_argument("--show-repos",
                   help="Lists all repositories within the specified project.",
                   default=False, action="store_true")
    p.add_argument("--show-branches",
                   help="Lists all branches in the specified repository.",
                   default=False, action="store_true")
    p.add_argument("--show-pullreqs",
                   help="Lists all Pull Requests in the specified repository.",
                   default=False, action="store_true")
    p.add_argument("--show-teams",
                   help="Lists all teams within the given project.",
                   default=False, action="store_true")
    p.add_argument("--show-backlogs",
                   help="List all backlogs for the corresponding team.",
                   default=False, action="store_true")
    
    # helper arguments
    p.add_argument("--show-config",
                   help="Lists all available configuration fields.",
                   default=False, action="store_true")
    p.add_argument("--show-env",
                   help="Lists all available environment variables.",
                   default=False, action="store_true")
                
    return p

def args_parse(parser: argparse.ArgumentParser):
    """
    Takes in the argument parser and returns parsed arguments.
    """
    a = vars(parser.parse_args())
    return a


# ================================= Helpers ================================== #
def help_show_config():
    """
    Lists all available config fields and their properties.
    """
    print("Top-level configuration fields: (%s*%s = required)" %
          (color("config_field_req"), color("none")))

    def print_field(key, f):
        # print the name and description
        msg_name = "%s%s%s" % (color("config_field_name"), f.name, color("none"))
        msg_desc = f.description
        msg_req = ""
        if f.required:
            msg_req = "%s*%s" % (color("config_field_req"), color("none"))
        print("%s%s%s - %s" % (str_tab(bullet=bullet_char), msg_name, msg_req, msg_desc))
        # print the field's other properties
        msg_types = "["
        for (i, t) in enumerate(f.types):
            msg_types += "%s%s%s" % (color("lime"), t.__name__, color("none"))
            if i < len(f.types) - 1:
                msg_types += ", "
        msg_types += "]"
        msg_default = "" if f.required else " (default: %s)" % str(f.default)
        print("%sAccepted types: %s%s" %
              (str_tab(count=2, bullet=bullet_char), msg_types, msg_default))

    # iterate across all fields in the main config
    config = config_load()
    for key in config.fields:
        print_field(key, config.fields[key])
        
    # show all fields from the event config
    print("\nMonitored event configuration fields:")
    c = EventConfig()
    for key in c.fields:
        print_field(key, c.fields[key])

    # show all fields from the event config
    print("\nMonitored event job configuration fields:")
    c = EventJobConfig()
    for key in c.fields:
        print_field(key, c.fields[key])

def help_show_env():
    """
    Lists all available environment variables.
    """
    print("All Available Environment Variables:")
    for key in env_vars:
        ev = env_vars[key]
        msg_name = "%s%s%s" % (color("env_name"), ev.name, color("none"))
        msg_desc = ev.description
        print("%s%s - %s" % (str_tab(bullet=bullet_char), msg_name, msg_desc))

def help_check():
    """
    Checks for the presence of any helper arguments. If one is specified, an
    action is carried out and the program exits.
    """
    if "show_config" in args and args["show_config"]:
        help_show_config()
        sys.exit(0)
    if "show_env" in args and args["show_env"]:
        help_show_env()
        sys.exit(0)

def help_intro():
    """
    Shows a helpful intro screen.
    """
    cb = color("ltblue")
    cn = color("none")
    print("Welcome to %sPLADO%s, a %sP%srogram %sL%sauncher for %sA%szure %sD%sev%sO%sps." %
          (cb, cn, cb, cn, cb, cn, cb, cn, cb, cn, cb, cn))
    
    # show the organization
    config = config_load()
    print("You are configured for the %s%s%s organization." %
          (color("organization"), config.get("ado_org"), color("none")))
    print("Run with %s-h%s/%s--help%s to see all available command-line options." %
          (color("gray"), cn, color("gray"), cn))
        
    # show the projects in the organization
    print("")
    ado_list_projects()


# ============================ Main Functionality ============================ #
def check_project(proj: any):
    """
    Takes in an object and does some basic checks to verify it's an ADO project
    object. Panics if it is not.
    """
    if proj is None:
        panic("You must specify a project name or ID via --project.")

def check_repo(repo: any):
    """
    Takes in an object and does some basic checks to verify it's an ADO repo
    object. Panics if it is not.
    """
    if repo is None:
        panic("You must specify a repository name or ID via --repo.")

def check_team(team: any):
    """
    Takes in an object and does some basic checks to verify it's an ADO team
    object. Panics if it is not.
    """
    if team is None:
        panic("You must specify a team name or ID via --team.")

def main():
    """
    Main function for the entire program.
    """
    # initialize environment variables
    env_init()

    # parse command-line arguments
    parser = args_init()
    global args
    args = args_parse(parser)
    
    # initialize color printing and look for the '--color' argument
    color_init()
    if "color" in args and args["color"]:
        color_setting = args["color"].strip().lower()
        if color_setting in ["on", "enable", "yes"]:
            color_enable()
        elif color_setting in ["off", "disable", "no"]:
            color_disable()
        else:
            panic("Unrecognized --color option: \"%s\"" % color_setting)

    # initialize debug
    dbg_init()

    # look for a config file path. Go with a default, but let it be overridden
    # by an environment variable OR '--config'
    config_path = config_path_default
    config_env = env("CONFIG")
    if config_env is not None:
        config_path = config_env
    if "config" in args and args["config"] is not None:
        config_path = args["config"]

    # make sure the config file exists, then attempt to load
    if not os.path.isfile(config_path):
        if config_path == config_path_default:
            return panic("Could not find a config file at the default location: %s" % config_path)
        else:
            return panic("The given config path could not be found: %s" % config_path)
    c = Config()
    try:
        c.parse_file(config_path)
    except Exception as e:
        return panic("Failed to load config.", exception=e)
    config_store(c)

    # check for the presence of any helper arguments
    help_check()

    # set up the connection to ADO
    try:
        ado_init()
    except Exception as e:
        panic("Failed to connect to ADO.", exception=e)
    
    # -------------------------- ADO Configuration --------------------------- #
    project = None
    if "project" in args and args["project"] is not None:
        project = ado_find_project(args["project"])
    repo = None
    if "repo" in args and args["repo"] is not None:
        check_project(project)
        repo = ado_find_repo(project, args["repo"])
    branch = None
    if "branch" in args and args["branch"] is not None:
        check_project(project)
        check_repo(repo)
        branch = ado_find_branch(project, repo, args["branch"])
    team = None
    if "team" in args and args["team"] is not None:
        check_project(project)
        team = ado_find_team(project, args["team"])
    backlog = None
    if "backlog" in args and args["backlog"] is not None:
        check_project(project)
        check_team(team)
        backlog = ado_find_backlog(project, team, args["backlog"])
    
    # ------------------------------- Routines ------------------------------- #
    if "show_projects" in args and args["show_projects"]:
        ado_list_projects()
        return 0
    if "show_repos" in args and args["show_repos"]:
        check_project(project)
        ado_list_repos(project)
        return 0
    if "show_branches" in args and args["show_branches"]:
        check_project(project)
        check_repo(repo)
        ado_list_branches(project, repo)
        return 0
    if "show_pullreqs" in args and args["show_pullreqs"]:
        check_project(project)
        check_repo(repo)
        ado_list_pullreqs(project, repo)
        return 0
    if "show_teams" in args and args["show_teams"]:
        check_project(project)
        ado_list_teams(project)
        return 0
    if "show_backlogs" in args and args["show_backlogs"]:
        check_project(project)
        check_team(team)
        ado_list_backlogs(project, team)
        return 0

    # ----------------------------- Monitor Mode ----------------------------- #
    # if monitor mode is specified, the program will transform into an event
    # monitoring daemon, designed to be run in the background
    if "monitor" in args and args["monitor"]:
        em_init()
        em_main()
        return 0

    # print out the project/repo/branch/etc. that was specified, if possible
    # (list all projects by default if nothing is specified)
    if branch is not None:
        ado_show_branch(project, repo, branch)
    elif repo is not None:
        ado_show_repo(project, repo)
    elif backlog is not None:
        ado_show_backlog(project, team, backlog)
    elif team is not None:
        ado_show_team(project, team)
    elif project is not None:
        ado_show_project(project)
    else:
        # if NOTHING is given besides the config, show a nice intro screen
        help_intro()
    
# ------------------------------- Runner Code -------------------------------- #
# Invoke the main routine
if __name__ == "__main__":
    main()

