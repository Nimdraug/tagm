# tagm

## Installation

Requires setuptools to be installed on your system.

`python2 setup.py install`

## Usage

    usage: tagm [-h] {init,add,get} ...

    optional arguments:
      -h, --help      show this help message and exit

    subcommands:
      {init,add,get}
        init          Will initialzie a tagm database in a file called .tagm.db
                      located in the current directory
        add           Will add the specified tags to the specified objects
        get           Will list all the objects that are taged with all of the
                      specified tags.

### Terms

|Term       |Description    |
|-----------|---------------|
|tag        |meta tag attached to an object|
|object     |file on the filesystem|
|tagpath    |the absolute path to a subtag going through each of its parent tags separated by colon.<br />colons can be escaped by a bachslash if they are supposed to be part of the tag|
|tagpaths   |list of tagpaths separated by comma|
|objects    |list of objects separated by comma or space|

### init

    usage: tagm init [-h]

    Will initialzie a tagm database in a file called .tagm.db located in the
    current directory

    optional arguments:
      -h, --help  show this help message and exit

### add

    usage: tagm add [-h] [-r] [-f] tags objs [objs ...]

    Will add the specified tags to the specified objects

    positional arguments:
      tags             List of tagpaths separated by comma
      objs             List of objects to be tagged

    optional arguments:
      -h, --help       show this help message and exit
      -r, --recursive  the list of objects is actually a list of recursive glob
                       paths
      -f, --no-follow  do not follow any symlinks

### get

    usage: tagm get [-h] [--tags] [--subtags] [--obj-tags] [tags [tags ...]]

    Will list all the objects that are taged with all of the specified tags.

    positional arguments:
      tags        list of tagpaths (or objects incase --obj-tags is used)
                  separated by comma

    optional arguments:
      -h, --help  show this help message and exit
      --tags      output the tags of the found objects instead of the objects
                  themselves
      --subtags   include subtags of the specified tags in the query
      --obj-tags  lookup the tags of the specified objects instead of the other
                  way around
