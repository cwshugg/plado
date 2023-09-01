# PLADO - "Painless Azure DevOps" Command-Line Interface

This contains code involving my idea for writing a command-line application that
interacts with the Azure DevOps API, using the official Microsoft Python API
(found [here](https://github.com/microsoft/azure-devops-python-api)).

## Design Plan

The program will be made up of multiple parts:

* **Environment Variable Bank** - This will define a number of environment
  variables that are used to configure the program.
    * `PLADO_CONFIG` - Can be used to set the default path to the user config.

* **Global Config** - This will define a number of fields that can be parsed
  through a user-written JSON file.
    * At runtime, it will parse a JSON file and search through it for the
      pre-defined fields.
    * Each field will be represented by a `ConfigField` object, which will have:
        * `name` - The name of the field.
        * `description` - The description of what the field is.
        * `types` - A list of acceptable types for this field.
        * `required` - A boolean indicating whether or not the field is required.
        * `default` - A default value that's used when the field isn't given.
        * `value` - The current value of the field.
    * The `Config` object will have a dictionary containing these fields,
      indexed by field name.
    * The `Config` object will have `get()` and `set()` functions, which use
      this dictionary to retrieve field values and update them.
        * When `set()` is invoked, if an unknown name is given, an error is
          thrown.
        * When `set()` is invoked, type-checking is done against the targeted
          `ConfigField` object to make sure the new value is appropriate.
    * The config will first pull from the environment variable `PLADO_CONFIG`,
      followed by `--config`, finally followed by the default location of
      `${HOME}/.plado_config.json`

* **Command-Line Arguments** - These will be used at runtime to pass in values
  for processing.
    * `-c` / `--config` - This will take in a path to a config file. It
      overrides the default config file path.

### Base Features

* Organization information
    * List projects
* Project information
    * List repos
* Repo information
    * List files
    * List PRs
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

* Callbacks/Jobs for certain events - Give users the ability to have this
  program run in a daemon-like mode that monitors for events such as:
    * New PR created in repo
    * New work item created
    * User assigned to PR reviewers
    * Work item assigned to user
    * etc.
    * Then, the program fires off a user-defined script/shell arguments,
      passing it some information to do with it what it pleases. This would
      be awesome for automation purposes.

* All things list-able will be filterable by regex

### Extra Features

Some extra ideas for features once the important stuff is done.

* `--show-config` - This argument will list all possible config fields, their
  descriptions, the acceptable types, whether or not it's required, etc.
* `--show-env` - This argument will list all possible environment variables accepted
  by the tool.

