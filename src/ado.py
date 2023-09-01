# This module implements code that interacts with Azure DevOps.

# Imports
import os
import sys
from datetime import datetime
import validators

# Path setup
srcdir = os.path.realpath(os.path.dirname(__file__))
if srcdir not in sys.path:
    sys.path.append(srcdir)

# Tool imports
from env import env
from config import config_load
from debug import dbg_print
from utils.colors import *
from utils.utils import *

# ADO imports
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

# Globals
conn = None         # global connection reference
c_core = None       # global core client
c_git = None        # global git client


# ========================== Connection Management =========================== #
def ado_init():
    """
    Establishes a connection with ADO, using the credentials given in the
    config.
    """
    conf = config_load()

    # create a URL to connect to (adjust based on if the URL was given, or just
    # the organization name)
    url = conf.get("ado_org")
    if not validators.url(url):
        dbg_print("ado", "Organization name: %s" % url)
        url = "https://dev.azure.com/%s" % url
    dbg_print("ado", "Organization URL: %s" % url)

    # create a credentials object for the PAT and esteablish a connection
    creds = BasicAuthentication("", conf.get("ado_pat"))
    global conn
    conn = Connection(base_url=url, creds=creds)
    
    # initialize core client
    ado_client_core()

def ado_client_core():
    """
    Returns an Azure DevOps core client object.
    """
    global c_core
    if c_core is None:
        c_core = conn.clients.get_core_client()
        dbg_print("ado", "Created core client.")
    return c_core

def ado_client_git():
    """
    Returns an Azure DevOps git client object.
    """
    global c_git
    if c_git is None:
        c_git = conn.clients.get_git_client()
        dbg_print("ado", "Created git client.")
    return c_git


# ================================= Lookups ================================== #
def ado_find_project(txt: str):
    """
    Takes in a project name or ID string and attempts to find a matching
    project. Panics if one isn't found.
    """
    cc = ado_client_core()
    try:
        dbg_print("ado", "Searching for project \"%s\"." % txt)
        proj = cc.get_project(txt)
        dbg_print("ado", "Found project with name \"%s%s%s\" and ID \"%s%s%s\"." %
                  (color("project"), proj.name, color("none"),
                   color(proj.id), proj.id, color("none")))
        return proj
    except Exception as e:
        panic("Failed to retrieve the project \"%s%s%s\"." %
              (color("project"), txt, color("none")), exception=e)

def ado_find_repo(proj, txt: str):
    """
    Takes in a project object and a repository ID/name string and attempts to
    find a matching repo. Panics if one isn't found.
    """
    cg = ado_client_git()
    try:
        dbg_print("ado", "Searching for repository: \"%s\"." % txt)
        repo = cg.get_repository(txt, project=proj.id)
        dbg_print("ado", "Found project with name \"%s%s%s\" and ID \"%s%s%s\"." %
                  (color("repo"), repo.name, color("none"),
                   color(repo.id), repo.id, color("none")))
        return repo
    except Exception as e:
        panic("Failed to retrieve the repository \"%s%s%s\" from project %s%s%s." %
              (color("repo"), txt, color("none"),
               color("project"), proj.name, color("none")), exception=e)

def ado_find_branch(proj, repo, txt: str):
    """
    Takes in a project and repository, and uses the given string to search for a
    branch inside the repository.
    """
    cg = ado_client_git()
    try:
        dbg_print("ado", "Searching for branch: \"%s\"." % txt)
        branch = cg.get_branch(repo.id, txt, project=proj.id)
        dbg_print("ado", "Found branch with name \"%s%s%s\"." %
                  (color("branch"), branch.name, color("none")))
        return branch
    except Exception as e:
        panic("Failed to retrieve the branch \"%s%s%s\" from repository %s%s%s." %
              (color("branch"), txt, color("none"),
               color("repo"), repo.name, color("none")), exception=e)

def ado_project_get_repos(proj):
    """
    Takes in a project and returns a list of all repositories within it.
    """
    cg = ado_client_git()
    try:
        repos = cg.get_repositories(proj.id)
        return repos
    except Exception as e:
        panic("Failed to retrieve repositories from project %s%s%s." %
              (color("project"), proj.name, color("none")))

def ado_repo_get_branches(proj, repo):
    """
    Takes in a project and repo and returns a list of all branches.
    """
    cg = ado_client_git()
    try:
        branches = cg.get_branches(repo.id, project=proj.id)
        return branches
    except Exception as e:
        panic("Failed to retrieve branches from repo %s%s%s." %
              (color("repo"), repo.name, color("none")))


# ================================= Features ================================= #
def ado_list_projects():
    """
    Displays a list of all projects within the organization.
    """
    cc = ado_client_core()
    projects = cc.get_projects()
    projects_len = len(projects)
    dbg_print("ado", "Loaded %d project(s)." % projects_len)

    # if none were found, exit early
    if projects_len == 0:
        print("No projects were found.")
        return
    
    print("Found %d project%s:" % (projects_len, "" if projects_len == 1 else "s"))
    for proj in projects:
        # get a shortened description of the project
        desc = proj.description
        if desc is None:
            desc = "%s(no description)%s" % (color("gray"), color("none"))
        else:
            desc = desc.split("\n")[0].strip()

        # print the project's details (with a shortened description)
        print("%s%s%s%s - %s" %
              (str_tab(bullet=bullet_char),
               color("project"), proj.name, color("none"),
               desc))

def ado_show_project(proj):
    """
    Takes in a project oject and displays information about it.
    """
    # print project name, ID, and revision
    print("%sProject:%s %s%s%s" %
          (color("gray"), color("none"),
           color("project"), proj.name, color("none")))
    print("%sID:%s %s%s%s" %
          (color("gray"), color("none"),
           color(proj.id), proj.id, color("none")))
    print("%sRevision:%s %s%s%s" %
          (color("gray"), color("none"),
           color("none"), proj.revision, color("none")))
    print("%sLast Updated:%s %s%s%s" %
          (color("gray"), color("none"),
           color("none"), proj.last_update_time, color("none")))
    
    # lastly, print the description
    print("%sDescription:%s %s" % (color("gray"), color("none"), proj.description))

def ado_list_repos(proj):
    """
    Takes in a project object and lists all of its repositories.
    """
    repos = ado_project_get_repos(proj)
    repos_len = len(repos)
    dbg_print("ado", "Loaded %d repositories." % repos_len)

    # alert the user if no repos were found
    if repos is None or len(repos) == 0:
        print("Could not find any repositories within project %s%s%s." %
              (color("project"), proj.name, color("none")))
        return
    
    # list all repositories in a bulleted list
    print("Found %d repositor%s:" % (repos_len, "y" if repos_len == 1 else "ies"))
    for repo in repos:
        print("%s%s%s%s - %s%s%s" %
              (str_tab(bullet=bullet_char),
              color("repo"), repo.name, color("none"),
              color("url"), repo.web_url, color("none")))

def ado_show_repo(proj, repo):
    """
    Takes in a project and repository and displays information about the repo.
    """
    # print repo name and add a note if it's disabled
    print("%sRepository:%s %s%s%s" %
          (color("gray"), color("none"),
           color("repo"), repo.name, color("none")), end="")
    if repo.is_disabled:
        print(" %s(DISABLED)%s" % (color("red"), color("none")))
    else:
        print("")
    
    # print repo ID and other stats
    print("%sID:%s %s%s%s" %
          (color("gray"), color("none"),
           color(repo.id), repo.id, color("none")))
    print("%sDefault Branch:%s %s%s%s" %
          (color("gray"), color("none"),
           color("none"), repo.default_branch, color("none")))
    print("%sSize:%s %s%s%s" %
          (color("gray"), color("none"),
           color("none"), str_file_size(repo.size), color("none")))
    print("%sWeb URL:%s %s%s%s" %
          (color("gray"), color("none"),
           color("url"), repo.web_url, color("none")))
    print("%sSSH URL:%s %s%s%s" %
          (color("gray"), color("none"),
           color("url"), repo.ssh_url, color("none")))
    print("%sAPI URL:%s %s%s%s" %
          (color("gray"), color("none"),
           color("url"), repo.url, color("none")))
    print("%sRemote URL:%s %s%s%s" %
          (color("gray"), color("none"),
           color("url"), repo.remote_url, color("none")))

def ado_list_repo_branches(proj, repo):
    """
    Shows a given repository's list of branches.
    """
    branches = ado_repo_get_branches(proj, repo)
    branches_len = len(branches)
    print("Found %d branch%s:" % (branches_len, "" if branches_len == 1 else "es"))
    
    # iterate through all branches
    for branch in branches:
        print("%s%s%s%s" %
              (str_tab(bullet=bullet_char),
              color("branch"), branch.name, color("none")), end="")
        
        # if the branch is behind, add to the line
        if branch.behind_count > 0:
            print(" (%s-%d%s)" %
                  (color("red"), branch.behind_count, color("none")), end="")

        # if the branch is ahead, add to the line
        if branch.ahead_count > 0:
            print(" (%s+%d%s)" %
                  (color("green"), branch.ahead_count, color("none")), end="")

        # end the line
        print("")

def ado_show_branch(proj, repo, branch):
    """
    Shows a given branch's information.
    """
    print("%sBranch:%s %s%s%s" %
          (color("gray"), color("none"),
           color("branch"), branch.name, color("none")))
    
    # print the ahead/behind states
    print("%sCommits:%s %s%d%s behind, %s%d%s ahead, of %s%s%s" %
          (color("gray"), color("none"),
           color("red"), branch.behind_count, color("none"),
           color("green"), branch.ahead_count, color("none"),
           color("branch"), repo.default_branch, color("none")))

    # print the latest commit
    commit = branch.commit
    print("%sLatest Commit - ID:%s %s%s%s" %
          (color("gray"), color("none"),
           color(commit.commit_id), commit.commit_id, color("none")))
    print("%sLatest Commit - Author Name:%s %s%s%s" %
          (color("gray"), color("none"),
           color("none"), commit.author.name, color("none")))
    print("%sLatest Commit - Author Email:%s %s%s%s" %
          (color("gray"), color("none"),
           color("none"), commit.author.email, color("none")))
    print("%sLatest Commit - Comment:%s %s%s%s" %
          (color("gray"), color("none"),
           color("none"), commit.comment, color("none")))

