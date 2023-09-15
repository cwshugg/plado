# PLADO - Program Launcher for Azure DevOps

This is a command-line utility I created to serve as an event monitoring daemon
for Azure DevOps. It accepts a single configuration file and monitors the
specified events. When an event is detected, it forks processes to run the jobs
you specify in the config file.

I created this as a way to automate certain DevOps-related processes at work.
(I created this during the 2023 Microsoft Hackathon.)

To communicate with Azre DevOps, this uses the official Python API found
[here](https://github.com/microsoft/azure-devops-python-api).

## Getting Started

To get started, clone the repository and install all requirements in the
requirements file:

```bash
git clone https://github.com/cwshugg/plado
cd ./plado
python3 -m pip install -r ./requirements.txt
```

Then, to run, simply invoke the `main.py` Python script. You'll need to specify
configuration file via `-c`/`--config` to begin using the script.

```bash
python3 src/main.py -c ./my_config.json
```

You can also use `-h`/`--help` to see all available command-line arguments:

```bash
python3 src/main.py -h
```

Once you've set up your configuration file to track events, invoke the program
with the `-m`/`--monitor` option to enable event-monitoring mode:

```bash
python3 src/main.py -c ./my_config.json -m
```

## Documentation

* TODO

## To Do List

* Documentation
    * Write markdown documentation
    * Write Linux man page
    * Example config file(s)
* Information retrieval
    * When displaying a team, display all of its members (use the core client's
      `get_team_members_with_extended_properties()` function)
    * Add `-u`/`--user` to display user IDs
* Polling optimization
    * Modify `Event_PR` and `Event_Branch` to poll only for the specified
      PR/branch when the user specifies a single PR/branch-of-interest
* Implement more events
    * `Event_WI`
        * `Event_WI_Create`
        * `Event_WI_Assigned`
        * `Event_WI_State_Change`
        * `Event_WI_Comment_Add`
        * `Event_WI_Comment_Edit`
        * ...
    * `Event_Pipeline`
        * `Event_Pipeline_Run_Start`
        * `Event_Pipeline_Run_End`
        * ...

* Update `--show-config` to find *all* objects that extend the base `Config`
  class and print out their options. (Add a `description` field to the `Config`
  class, to be printed for each different Config subclass to help describe
  where it's used)
* Add JSON versions of all `--show` arguments (i.e. `--show-pullreqs-json`),
  which performs the same operations, but dumps out the raw JSON from ADO

