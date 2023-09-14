# PLADO - Program Launcher for Azure DevOps

This is a command-line utility I created to serve as an event monitoring daemon
for Azure DevOps. It accepts a single configuration file and monitors the
specified events. When an event is detected, it forks processes to run the jobs
you specify in the config file.

I created this as a way to automate certain DevOps-related processes at work.
(I created this during the 2023 Microsoft Hackathon.)

To communicate with Azre DevOps, this uses the official Python API found
[here](https://github.com/microsoft/azure-devops-python-api).

## Documentation

* TODO

## To Do List

* Documentation
    * Write markdown documentation
    * Write Linux man page
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

