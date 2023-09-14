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

Before running, make sure to install all dependencies from the requirements file:

```bash
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

## Documentation

* TODO

## To Do List

* Documentation
    * Write markdown documentation
    * Write Linux man page
    * Example config file(s)
* Implement more events
    * `Event_WI`
        * `Event_WI_Create`
        * `Event_WI_Assigned`
        * `Event_WI_State_Change`
        * `Event_WI_Comment_Add`
        * `Event_WI_Comment_Edit`
        * ...
    * `Event_Pipeline`
        * ...

* Update `--show-config` to find *all* objects that extend the base `Config`
  class and print out their options. (Add a `description` field to the `Config`
  class, to be printed for each different Config subclass to help describe
  where it's used)
* Add JSON versions of all `--show` arguments (i.e. `--show-pullreqs-json`),
  which performs the same operations, but dumps out the raw JSON from ADO

