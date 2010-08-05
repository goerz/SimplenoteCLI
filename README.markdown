# SimplenoteCLI

[http://github.com/goerz/SimplenoteCLI](http://github.com/goerz/SimplenoteCLI)

Author: [Michael Goerz](http://michaelgoerz.net)

SimplenoteCLI is a command line tool that provides access to the
[Simplenote][1]. It consists of `SimplenoteCLI.py`, which is a python wrapper
around the Simplenote API, as well as a independent CLI script, and
`simplenote.vim`, which is a [vim][2] plugin (depending on `SimplenoteCLI.py`)
for editing and managing notes in vim.

[1]: http://simplenoteapp.com
[2]: http://www.vim.org

This code is licensed under the [GPL](http://www.gnu.org/licenses/gpl.html)

## Install ##

Save the `SimplenoteCLI.py` script somewhere in your `$PATH` if you want to use
it as a command line tool. If you only want to use it as a backend for the vim
plugin, you can place it anywhere, e.g. `~/.vim/scripts/`.

Save the `simplenote.vim` script in `~/.vim/plugin/`. Edit the file to set
the `s:simplenote_bin` variable to point to the `SimplenoteCLI.py` script.

## Dependencies ##

* [simplejson >= 2.1.1][3]

[3]: http://code.google.com/p/simplejson/

## Usage ##

### Using SimplenoteCLI.py as a Command Line Tool ###

    Usage: SimplenoteCLI.py [options] CMD ARGS


    Executes given CMD, where CMD is one of the following, along with
    correspondings ARGS:

    list [FILENAME]               -  write list of all notes to FILENAME
                                     (or print to stdout if FILENAME not given)
    search SEARCHTERM  [FILENAME] -  write list of notes matching SEARCHTERM to
                                     FILENAME (or print to stdout if FILENAME
                                     not given)
    read KEY FILENAME             -  store note with KEY in FILENAME
    write KEY FILENAME            -  update note with KEY with data from FILENAME
    new FILENAME                  -  create new note from FILENAME
    delete KEY                    -  delete note with KEY


    Options:
      -h, --help            show this help message and exit
      --email=EMAIL         Email address to use for authentification
      --password=PASSWORD   Password to use for authentification (Read warning
                            below).
      --credfile=CREDFILE   File from which to read email (first line) and
                            password (second line). Defaults to
                            ~/.simplenotesyncrc
      --cachefile=CACHEFILE
                            File in which to cache information about notes. Using
                            a cachefile can dramatically speed up listing notes.
      --tokenfile=TOKENFILE
                            File in which to cache the authentication token
      --results=RESULTS     Maximum number of results to be returned in a search
      --encoding=ENCODING   Encoding for notes written to file or read from file
                            (defaults to utf-8).
      --dead                When deleting a note, delete it permanently

    You are strongly advised to use the --credfile option instead of the
    --password option. Giving a password in cleartext on the command line will
    result in that password being visible in the process list and your history
    file.

### Using SimplenoteCLI.py as a Python API wrapper ###

To get information about the API implemented in SimplenoteCLI.py, start
`python` in the same directory as `SimplenoteCLI.py`, and type in

    import SimplenoteCLI
    help(SimplenoteCLI)

### Using the Vim Plugin ###

In vim, enter

    :Simplenote

to get a listing of all notes. Use the shortcuts given at the top of the screen
to edit, add, delete notes.
