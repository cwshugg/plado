# PLADO - Program Launcher for Azure DevOps

This contains code involving my idea for writing a command-line application that
interacts with the Azure DevOps API, using the official Microsoft Python API
(found [here](https://github.com/microsoft/azure-devops-python-api)).

## Name Ideas

* PLADO is a cool acronym, but it's not really that meaningful if it's just
  "painless". Could it mean something else?
    * Perhaps "Perceiver of L\_\_\_ on Azure DevOps" (what would "L" stand for?)
    * Ahh, got it: "Program Launcher for Azure DevOps". Duh.
* What about "ADOMate"? It's got ADO in the name, is a play on the word
  "automate" (which is what the tool does), and "mate" makes it sound like
  the tool is your buddy that helps you out

## ToDos

* Implement events
    * `Event_PR`
        * `Event_PR_Comment_New`
        * `Event_PR_Comment_Update`
        * `Event_PR_Comment_Resolved`
        * `Event_PR_Comment_Reactivated`
        * `Event_PR_Merged`
    * `Event_WI`
        * TODO
    * `Event_Pipeline`
        * TODO

* Update `--show-config` to find *all* objects that extend the base `Config`
  class and print out their options. (Add a `description` field to the `Config`
  class, to be printed for each different Config subclass to help describe
  where it's used)
* Add JSON versions of all `--show` arguments (i.e. `--show-pullreqs-json`),
  which performs the same operations, but dumps out the raw JSON from ADO

### Base Features

* Organization information
    * List projects (DONE)
* Project information
    * List repos (DONE)
* Repo information
    * List files
    * List PRs (DONE)
        * Show PR info (creator, description, list files, etc.)
        * Show PR builds that are running (and their statuses)
        * Show PR discussion (comments)
    * List contributors
* Pipeline information
    * Show which ones are running
    * Show pass rates
    * Show fail buckets
* Work Item information (boards)
    * Show all work items assigned to a user

* Callbacks/Jobs for certain events ("Event Monitoring") - Give users the ability to have this
  program run in a daemon-like mode that monitors for events such as:
    * New PR created in repo
    * New work item created
    * User assigned to PR reviewers
    * Work item assigned to user
    * etc.
    * Then, the program fires off a user-defined script/shell arguments,
      passing it some information to do with it what it pleases. This would
      be awesome for automation purposes.
    * Examples for why this may be useful:
        * Every time a specific user creates a PR, you want to run a script that
          clones the repo, checks out the branch, and does some work.
        * Every time a work item is created under a specific group, run a script
          that searches it for keywords and asign it to a certain person.
        * Every time a pipeline is started, write it to a log file.
    * Examples I personally want to use:
        * Use this to automatically log *all* of my ADO activity (pushed commits,
          PR interactions, WI interactions, pipeline runs, etc.)
        * Every time I create a work item, add a comment that @'s my teammates

* All things list-able will be filterable by regex

