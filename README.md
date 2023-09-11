# PLADO - "Painless Azure DevOps" Command-Line Interface

This contains code involving my idea for writing a command-line application that
interacts with the Azure DevOps API, using the official Microsoft Python API
(found [here](https://github.com/microsoft/azure-devops-python-api)).

## Name Ideas

* PLADO is a cool acronym, but it's not really that meaningful if it's just
  "painless"
* What about "ADOMate"? It's got ADO in the name, is a play on the word
  "automate" (which is what the tool does), and "mate" makes it sound like
  the tool is your buddy that helps you out

## Design Plans

* Event Monitoring
    * Define a base class, called, `Event`, that has various parameters
        * `name` - name of the event (basically the class name, converted to lowercase, minus the `"Event_"`)
        * `fire_params` - command-line arguments with which to fire off a task once an event triggers
        * ... TODO
    * Then, extend this base class into various other events:
        * `Event_PR`
            * `Event_PR_Create`
            * `Event_PR_StatusChange`
            * `Event_PR_Comment_Create`
            * ...
        * `Event_WI`
            * `Event_WI_Create`
            * `Event_WI_Assign`
            * `Event_WI_StatusChange`
            * ...
        * `Event_Pipeline`
            * `Event_Pipeline_Launch`
            * `Event_Pipeline_Finish`
            * ...
    * Each event class has their own set of parameters that must be given via
      the config JSON file

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

#### Command-Line Options

* `--format` - This sets the output format for any given object being dumped
  to the terminal. Options are:
    * `pretty` - The default option, which uses colors and nice formatting to
      show the information in a pleasant way
    * `json` - Outputs *only* JSON, so it can be easily parsed by a machine.

### Extra Features

Some extra ideas for features once the important stuff is done.

* Threading: implement daemon mode to have a configurable number of threads
  that events can be sent to for processing.

