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
from azure.devops.v7_1.work.models import TeamContext
from azure.devops.v7_1.git.models import GitQueryCommitsCriteria
from msrest.authentication import BasicAuthentication

# Globals
conn = None         # global connection reference
c_core = None       # global core client
c_git = None        # global git client
c_work = None       # global work client


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

def ado_client_work():
    """
    Returns an Azure DevOps work client object.
    """
    global c_work
    if c_work is None:
        c_work = conn.clients.get_work_client()
        dbg_print("ado", "Created work client.")
    return c_work


# ================================= Lookups ================================== #
def ado_find_project(txt: str):
    """
    Takes in a project name or ID string and attempts to find a matching
    project. Panics if one isn't found.
    """
    cc = ado_client_core()
    try:
        proj = cc.get_project(txt)
        if proj is not None:
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
        repo = cg.get_repository(txt, project=proj.id)
        if repo is not None:
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
        branch = cg.get_branch(repo.id, txt, project=proj.id)
        if branch is not None:
            dbg_print("ado", "Found branch with name \"%s%s%s\"." %
                      (color("branch"), branch.name, color("none")))
        return branch
    except Exception as e:
        panic("Failed to retrieve the branch \"%s%s%s\" from repository %s%s%s." %
              (color("branch"), txt, color("none"),
               color("repo"), repo.name, color("none")), exception=e)

def ado_find_pullreq(proj, repo, txt: str):
    """
    Searches for a pull request given the name or ID string and returns it.
    """
    cg = ado_client_git()
    try:
        pr = cg.get_pull_request(repo.id, txt, project=proj.id)
        if pr is not None:
            dbg_print("ado", "Found Pull Request with ID %s%s%s." %
                      (color("pullreq_id"), pr.pull_request_id, color("none")))
        return pr
    except Exception as e:
        panic("Failed to retrieve the Pull Request \"%s%s%s\" from repository %s%s%s." %
              (color("pullreq_id"), txt, color("none"),
               color("repo"), repo.name, color("none")), exception=e)

def ado_find_team(proj, txt: str):
    """
    Takes in a project and team name/ID and searches for the matching team.
    """
    cc = ado_client_core()
    try:
        team = cc.get_team(proj.id, txt)
        if team is not None:
            dbg_print("ado", "Found team with name \"%s%s%s\" and ID \"%s%s%s\"." %
                      (color("team"), team.name, color("none"),
                       color(team.id), team.id, color("none")))
        return team
    except Exception as e:
        panic("Failed to retrieve the team \"%s%s%s\"." %
              (color("team"), txt, color("none")), exception=e)

def ado_find_backlog(proj, team, txt: str):
    """
    Takes in a team and retrieves a backlog based on the given text.
    """
    cw = ado_client_work()
    try:
        # create a TeamContext object from the team object
        tc = TeamContext(project=proj,
                         project_id=proj.id,
                         team=team,
                         team_id=team.id)

        bl = cw.get_backlog(tc, txt)
        if bl is not None:
            dbg_print("ado", "Found backlog \"%s%s%s\"." %
                      (color("backlog"), bl.name, color("none")))
        return bl
    except Exception as e:
        panic("Failed to retrieve the backlog \"%s%s%s\"." %
              (color("backlog"), txt, color("none")), exception=e)

def ado_project_get_repos(proj):
    """
    Takes in a project and returns a list of all repositories within it.
    """
    cg = ado_client_git()
    try:
        repos = cg.get_repositories(proj.id)
        if repos is not None:
            dbg_print("ado", "Found %d repositories in project %s%s%s." %
                      (len(repos), color("project"), proj.name, color("none")))
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
        if branches is not None:
            dbg_print("ado", "Found %d branches in repository %s%s%s." %
                      (len(branches), color("repo"), repo.name, color("none")))
        return branches
    except Exception as e:
        panic("Failed to retrieve branches from repo %s%s%s." %
              (color("repo"), repo.name, color("none")), exception=e)

def ado_repo_get_commits(proj, repo, search_criteria=None):
    """
    Takes in a project and repo and retrieves commits.
    Optional search criteria can be specified.
    """
    cg = ado_client_git()
    try:
        commits = cg.get_commits(repo.id, search_criteria, project=proj.id)
        if commits is not None:
            dbg_print("ado", "Found %d commits for repository %s%s%s." %
                      (len(commits), color("repo"), repo.name, color("none")))
        return commits
    except Exception as e:
        panic("Failed to retrieve commits from repo %s%s%s." %
              (color("repo"), repo.name, color("none")), exception=e)

def ado_repo_get_pullreqs(proj, repo):
    """
    Takes in a project and repo and returns a list of all pull requests.
    """
    cg = ado_client_git()
    try:
        search_criteria = None
        prs = cg.get_pull_requests(repo.id, search_criteria, project=proj.id)
        if prs is not None:
            dbg_print("ado", "Found %d pull requests in repository %s%s%s." %
                      (len(prs), color("repo"), repo.name, color("none")))
        return prs
    except Exception as e:
        panic("Failed to retrieve pull requests from repo %s%s%s." %
              (color("repo"), repo.name, color("none")), exception=e)

def ado_pullreq_get_threads(proj, repo, pr):
    """
    Takes in a project, repo, and PR, and retrieve and returns a list of
    threads in the pull request.
    """
    cg = ado_client_git()
    try:
        thrds = cg.get_threads(repo.id, pr.pull_request_id, project=proj.id)
        if thrds is not None:
            dbg_print("ado", "Found %d threads in PR %s%s%s." %
                      (len(thrds), color("pullreq_id"), pr.pull_request_id, color("none")))
        return thrds
    except Exception as e:
        panic("Failed to retrieve threads from PR %s%s%s." %
              (color("pullreq_id"), pr.pull_request_id, color("none")), exception=e)

def ado_project_get_teams(proj):
    """
    Takes in a project and retrieves its teams.
    """
    cc = ado_client_core()
    try:
        teams = cc.get_teams(proj.id)
        if teams is not None:
            dbg_print("ado", "Found %d teams in project %s%s%s." %
                      (len(teams), color("project"), proj.name, color("none")))
        return teams
    except Exception as e:
        panic("Failed to retrieve teams from project %s%s%s." %
              (color("project"), proj.name, color("none")), exception=e)

def ado_team_get_backlogs(proj, team):
    """
    Takes in a team and retrieves its backlogs.
    """
    cw = ado_client_work()
    try:
        # create a TeamContext object from the team object
        tc = TeamContext(project=proj,
                         project_id=proj.id,
                         team=team,
                         team_id=team.id)

        bls = cw.get_backlogs(tc)
        if bls is not None:
            dbg_print("ado", "Found %d backlogs for team %s%s%s." %
                      (len(bls), color("team"), team.name, color("none")))
        return bls
    except Exception as e:
        panic("Failed to retrieve backlogs from team %s%s%s." %
              (color("team"), team.name, color("none")), exception=e)

def ado_team_get_members(proj, team):
    """
    Takes in a team and retrieves its members.
    """
    cc = ado_client_core()
    try:
        mbrs = cc.get_team_members_with_extended_properties(proj.id, team.id)
        if mbrs is not None:
            dbg_print("ado", "Found %d members for team %s%s%s." %
                      (len(mbrs), color("team"), team.name, color("none")))
        return mbrs
    except Exception as e:
        panic("Failed to retrieve members from team %s%s%s." %
              (color("team"), team.name, color("none")), exception=e)

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

def ado_list_branches(proj, repo):
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
    behind_color = color("red") if branch.behind_count > 0 else color("none")
    ahead_color = color("green") if branch.ahead_count > 0 else color("none")
    print("%sCommits:%s %s%d%s behind, %s%d%s ahead, of %s%s%s" %
          (color("gray"), color("none"),
           behind_color, branch.behind_count, color("none"),
           ahead_color, branch.ahead_count, color("none"),
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

def ado_list_pullreqs(proj, repo):
    """
    Lists the given repository's pull requests.
    """
    prs = ado_repo_get_pullreqs(proj, repo)
    prs_len = len(prs)
    print("Found %d pull request%s:" % (prs_len, "" if prs_len == 1 else "s"))
    
    # iterate through all branches
    for pr in prs:
        print("%s%s%s%s - %s%s%s (%s%s%s --> %s%s%s)" %
              (str_tab(bullet=bullet_char),
              color("pullreq_id"), str(pr.pull_request_id), color("none"),
              color("pullreq_owner"), pr.created_by.unique_name, color("none"),
              color("pullreq_branch_src"), pr.source_ref_name, color("gray"),
              color("pullreq_branch_dst"), pr.target_ref_name, color("none")))

def ado_list_teams(proj):
    """
    Lists the given project's teams.
    """
    teams = ado_project_get_teams(proj)
    teams_len = len(teams)
    print("Found %d team%s:" % (teams_len, "" if teams_len == 1 else "s"))

    for team in teams:
        desc = team.description.strip().split("\n")[0]
        if desc is None or len(desc) == 0:
            desc = "%s(no description)%s" % (color("dkgray"), color("none"))

        print("%s%s%s%s - %s%s%s" %
              (str_tab(bullet=bullet_char),
               color("team"), str(team.name), color("none"),
               color("none"), desc, color("none")))

def ado_show_team(proj, team):
    """
    Displays information about the given team.
    """
    print("%sTeam:%s %s%s%s" %
          (color("gray"), color("none"),
           color("team"), team.name, color("none")))
    
    # print team info
    print("%sID:%s %s%s%s" %
          (color("gray"), color("none"),
           color(team.id), team.id, color("none")))

    # print the team's description
    desc = team.description.strip()
    if desc is None or len(desc) == 0:
        desc = "%s(no description)%s" % (color("dkgray"), color("none"))
    print("%sDescription:%s %s%s%s" %
          (color("gray"), color("none"),
           color("none"), desc, color("none")))

    # print the team's member count
    members = ado_team_get_members(proj, team)
    members_len = len(members)
    print("%sTeam Members:%s %d member%s" %
          (color("gray"), color("none"),
           members_len,
           "" if members_len == 1 else "s"))
    
    # list the team members
    for mbr in members:
        user = mbr.identity
        print("%s%s%s%s - %s%s%s - %s%s%s" %
              (str_tab(bullet=bullet_char),
               color("user_displayname"), user.display_name, color("none"),
               color("user_uniquename"), user.unique_name, color("none"),
               color("user_id"), user.id, color("none")))

def ado_list_backlogs(proj, team):
    """
    Lists the given team's backlogs.
    """
    bls = ado_team_get_backlogs(proj, team)
    bls_len = len(bls)
    print("Found %d backlog%s:" % (bls_len, "" if bls_len == 1 else "s"))

    for bl in bls:
        # extract the color, if it has it
        blcolor = color("backlog")
        if hasattr(bl, "color"):
            blcolor = color_hex(str(bl.color))

        print("%s%s%s%s - %s%s%s - Rank: %s%s%s - Type: %s%s%s" %
              (str_tab(bullet=bullet_char),
              blcolor, bl.name, color("none"),
              color("backlog_id"), str(bl.id), color("none"),
              color("backlog_rank"), str(bl.rank), color("none"),
              color("backlog_type"), bl.type, color("none")))

def ado_show_backlog(proj, team, bl):
    """
    Displays information on the given backlog.
    """
    # extract the color, if it has it
    blcolor = color("backlog")
    if hasattr(bl, "color"):
        blcolor = color_hex(str(bl.color))

    print("%sBacklog:%s %s%s%s" %
          (color("gray"), color("none"),
           blcolor, bl.name, color("none")))
    print("%sID:%s %s%s%s" %
          (color("gray"), color("none"),
           color("backlog_id"), bl.id, color("none")))
    print("%sRank:%s %s%s%s" %
          (color("gray"), color("none"),
           color("backlog_rank"), str(bl.rank), color("none")))
    print("%sType:%s %s%s%s" %
          (color("gray"), color("none"),
           color("backlog_type"), bl.type, color("none")))

    # print all work item types
    print("%sWork Item Types:%s" %
          (color("gray"), color("none")))
    for wit in bl.work_item_types:
        # print an indicator if this is the default type
        default_str = ""
        if wit.name == bl.default_work_item_type.name:
            default_str = " %s(default)%s" % (color("gray"), color("none"))

        print("%s%s%s%s%s" %
              (str_tab(bullet=bullet_char),
              color("backlog_wi_type"), wit.name, color("none"),
              default_str))

