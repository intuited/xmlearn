`xmlearn`
=========

Library and CLI for learning about XML formats.
-----------------------------------------------

`xmlearn` is a python module and command line utility which can be used to glean information about the structure of an XML document.

The CLI commands map more or less directly to python functions.

There are some lower-level python functions which are not provided as CLI commands.

A major goal when developing this module was to learn about XML and Python support for it.  I suspect that many of its functions are already better implemented elsewhere.  Any suggestions are likely welcome.

### Distribution
The code is maintained as a [repository] at http://github.com.

### License
This code is copyright 2010 Ted Tibbetts and is licensed under the GNU Public License.  See the file COPYING for details.

### Dependencies
Requires [lxml] for all functionality.

Requires [python-graph], [python-graph-dot], and [pydot] for graphing.

The CLI uses the [argparse] module.  Note that argparse is included with Python 2.7.

Only tested with Python 2.6.

----------

### CLI
There are three CLI commands.

The global `-i` option is used to pass an input file; this defaults to `stdin`.

All three operate within the scope of an XPath provided by the global `-p` option; this path defaults to the root.

    usage: xmlearn [-h] [-i INFILE] [-p PATH] {graph,dump,tags} ...

    optional arguments:
      -h, --help            show this help message and exit
      -i INFILE, --infile INFILE
                            The XML file to learn about. Defaults to stdin.
      -p PATH, --path PATH  An XPath to be applied to various actions. Defaults to the root node.

#### dump
The `dump` functionality pretty-prints the structure of the document under a given XPath.

    usage: xmlearn dump [-h] [-l [RULESET]] [-r {full}] [-d MAXDEPTH] [-w WIDTH] [-v]

    Dump xml data according to a set of rules.

    optional arguments:
      -h, --help            show this help message and exit
      -l [RULESET], --list-rulesets [RULESET]
                            Get a list of rulesets or information about a particular ruleset
      -r {full}, --ruleset {full}
                            Which set of rules to apply. Defaults to "full".
      -d MAXDEPTH, --maxdepth MAXDEPTH
                            How many levels to dump.
      -w WIDTH, --width WIDTH
                            The output width of the dump.
      -v, --verbose         Enable verbose ruleset list. Only useful with `-l`.

#### tags
`tags` provides info about the tags used in the document.  Currently it can present either a list of tags or the list of tags which are children of a given tag.

    usage: xmlearn tags [-h] [-e] [-C] [-c [PARENT]]

    Show information about tags.

    optional arguments:
      -h, --help            show this help message and exit
      -e, --show-element    Enables display of the element path.
                            Without this option, data from multiple matching elements
                              will be listed in unbroken series.
                            This is mostly useful when the path selects multiple elements.
      -C, --no-combine      Do not combine results from various path elements.
                            This option is only meaningful when the --path leads to multiple elements.
      -c [PARENT], --child [PARENT]
                            List all tags which appear as children of PARENT.

#### graph
Builds an image file containing a graph of the tag relationships within the XML document.

Any formats supported by `pydot` can be used for the resulting image file.

    usage: xmlearn graph [-h] [--format FORMAT] [-F FORCE_EXTENSION] outfile

    Build a graph from the XML tags relationships.

    positional arguments:
      outfile               The filename for the graph image. If no --format is given,
                              it will be based on this name.

    optional arguments:
      -h, --help            show this help message and exit
      --format FORMAT       The format for the graph image.
                            It will be appended to the filename unless they already concur or -F is passed.
      -F FORCE_EXTENSION, --force-extension FORCE_EXTENSION
                            Allow the filename extension to differ from the file format.
                            Without this option, the format extension will be appended to the filename.

[repository]: http://github.com/intuited/xmlearn

[lxml]: http://pypi.python.org/pypi/lxml
[python-graph]: http://pypi.python.org/pypi/python-graph/1.7.0
[python-graph-dot]: http://pypi.python.org/pypi/python-graph-dot/1.7.0
[pydot]: http://pypi.python.org/pypi/pydot/1.0.2
[argparse]: http://pypi.python.org/pypi/argparse/1.1
