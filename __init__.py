#!/usr/bin/env python
"""Routines to parse mpd's protocol documentation."""
# TODO: refactor almost the entirety of this code into
#         a general-purpose library not targeted at MPD.

# TODO: rename this class `Dumper`.
class LXML_Dumper(object):
    """Dump an lxml.etree tree starting at `element`.
    
    Attributes:
        maxdepth: the maximum recursion level.
        width: the width at which text will be wrapped.
        ruleset: either a string matching one of the keys of rulesets,
                 or a Mapping containing such a ruleset.

    For now, this function is just useful for sussing out the shape of the XML.

    Setup:
        >>> import lxml.etree as etree
        >>> book = etree.parse('protocol.xml').getroot()
        >>> dumper = LXML_Dumper(maxdepth=2)
        >>> dumper.dump(book)
        The Music Player Daemon protocol (/book):
        [title] (/book/title): The Music Player Daemon protocol
        General protocol syntax (/book/chapter[1]):
            [title] (/book/chapter[1]/title): General protocol syntax
            Requests (/book/chapter[1]/section[1])
            Responses (/book/chapter[1]/section[2])
            Command lists (/book/chapter[1]/section[3])
            Ranges (/book/chapter[1]/section[4])
        Command reference (/book/chapter[2]):
            [title] (/book/chapter[2]/title): Command reference
            [note] (/book/chapter[2]/note):
            Querying MPD's status (/book/chapter[2]/section[1])
            Playback options (/book/chapter[2]/section[2])
            Controlling playback (/book/chapter[2]/section[3])
            The current playlist (/book/chapter[2]/section[4])
            Stored playlists (/book/chapter[2]/section[5])
            The music database (/book/chapter[2]/section[6])
            Stickers (/book/chapter[2]/section[7])
            Connection settings (/book/chapter[2]/section[8])
            Audio output devices (/book/chapter[2]/section[9])
            Reflection (/book/chapter[2]/section[10])
        >>> for c in book.iterdescendants('section'):
        ...     dumper.dump(c, maxdepth=0, ruleset='full')
        Requests (/book/chapter[1]/section[1]):
        Responses (/book/chapter[1]/section[2]):
        Command lists (/book/chapter[1]/section[3]):
        Ranges (/book/chapter[1]/section[4]):
        Querying MPD's status (/book/chapter[2]/section[1]):
        Playback options (/book/chapter[2]/section[2]):
        Controlling playback (/book/chapter[2]/section[3]):
        The current playlist (/book/chapter[2]/section[4]):
        Stored playlists (/book/chapter[2]/section[5]):
        The music database (/book/chapter[2]/section[6]):
        Stickers (/book/chapter[2]/section[7]):
        Connection settings (/book/chapter[2]/section[8]):
        Audio output devices (/book/chapter[2]/section[9]):
        Reflection (/book/chapter[2]/section[10]):

    """

    # Each ruleset maps tags to kwargs for `format_element`.
    rulesets = {'book': {'section': {'with_text': False},
                         'para': {'linebreak': True},
                         None: {'recurse': True}},
                'full': {None: {'recurse': True}}}
    default_ruleset = 'book'
    from sys import stdout
    from pprint import PrettyPrinter
    pformat = PrettyPrinter(indent=2).pformat
    @classmethod
    def print_rulesets(cls, ruleset=None, outstream=stdout,
                            format=pformat, verbose=False):
        """Output ruleset information.

        If a `ruleset` is given, that ruleset's rules are output.
        If no `ruleset` is given, a list of rulesets is output.
        
        The `verbose` option will cause full ruleset information
          to be given in the list of rulesets.

        `format` can be used to specify a different formatting function.
        """

        if ruleset:
            outstream.write(format(cls.rulesets[ruleset]))
        else:
            if verbose:
                outstream.write(format(cls.rulesets))
            else:
                outstream.writelines("\n".join(cls.rulesets.keys()))
        outstream.write("\n")

    maxdepth = None
    width = 80
    ruleset = rulesets['book']

    def __init__(self, **kwargs):
        """Initialize object attributes documented in the class docstring."""
        self.__dict__.update(kwargs)

    def relwrap(self, *args, **kwargs):
        """Wrap the text with an indent relative to the `depth` keyword arg.

        The text is indented 4 spaces for each level of depth.
        Wrapped lines are indented an extra 2 spaces.
        """
        from textwrap import wrap
        depth = kwargs.pop('depth', 0)
        wrap_kwargs = dict({'initial_indent': '    ' * depth,
                            'subsequent_indent': '    ' * depth + '  '})
        if hasattr(self, 'width'):
            wrap_kwargs.update(width=self.width)
        wrap_kwargs.update(kwargs)
        return "\n".join(wrap(*args, **wrap_kwargs))

    def format_element(self, element, depth, linebreak=False, with_text=True):
        from textwrap import dedent
        title = getattr(element.find('title'), 'text', '')
        title = title if title else '[{0}]'.format(element.tag)
        path = element.getroottree().getpath(element)
        eltext = getattr(element, 'text', '')
        eltext = dedent(eltext if eltext else '')
        if linebreak:
            summary = "{0} ({1}):".format(title, path)
            return "\n".join([self.relwrap(summary, depth=depth),
                              self.relwrap(eltext, depth=depth+1)])
        else:
            fmt = "{0} ({1}): {2}" if with_text else "{0} ({1})"
            return self.relwrap(fmt.format(title, path, eltext), depth=depth)

    # TODO: this function should take an output stream.
    def dump(self, element, **kwargs):
        """Dump `element` according to `ruleset`.
        
        Keyword arguments:
            depth: the initial depth of the dump.  Normally this will be 0.

            Additionally, the `maxdepth` and `ruleset` object keyword arguments
              can be overridden.
        """
        from copy import copy
        from collections import Mapping

        depth = kwargs.pop('depth', 0)
        maxdepth, ruleset = (kwargs.pop(a, getattr(self, a))
                           for a in ('maxdepth', 'ruleset'))

        if isinstance(ruleset, Mapping):
            pass
        elif isinstance(ruleset, basestring):
            ruleset = self.rulesets[ruleset]
        assert isinstance(ruleset, Mapping)

        def _dump(element, depth=0):
            for rule in ruleset.iteritems():
                if rule[0] == None:
                    default = copy(rule[1])
                elif rule[0] == element.tag:
                    kwargs = copy(rule[1])
                    break
            else:
                assert vars().has_key('default')
                kwargs = default

            recurse = kwargs.pop('recurse', False)
            print self.format_element(element, depth, **kwargs)
            if recurse:
                if (maxdepth is None or maxdepth > depth):
                    for child in element.getchildren():
                        _dump(child, depth + 1)

        _dump(element, depth=depth)

    def iter_unique_child_tags(self, root, tag):
        """Iterates through unique child tags for all instances of `tag`.

        Iteration starts at `root`.
        """
        found_child_tags = set()
        instances = root.iterdescendants(tag)
        from itertools import chain
        child_nodes = chain.from_iterable(i.getchildren() for i in instances)
        child_tags = (n.tag for n in child_nodes)
        for t in child_tags:
            if t not in found_child_tags:
                found_child_tags.add(t)
                yield t

    def iter_tag_list(self, root):
        """List all unique tags at and under the `root` node."""
        found_tags = set()
        tags = (n.tag for n in root.iterdescendants() if hasattr(n, 'tag'))
        for t in tags:
            if t not in found_tags:
                found_tags.add(t)
                yield t

    def build_tag_graph(self, root):
        """Build a python-graph graph of the tag relationships."""
        from pygraph.classes.digraph import digraph

        g = digraph()

        tags = list(self.iter_tag_list(root))
        g.add_nodes(tags)

        for parent in tags:
            for child in self.iter_unique_child_tags(root, parent):
                g.add_edge((parent, child))

        return g

    def write_graph(self, graph, filename, format='png'):
        """Write a python-graph graph as an image.

        `format` can be any of those supported by pydot.Dot.write().
        """
        from pygraph.readwrite.dot import write
        dotdata = write(graph)

        from pydot import graph_from_dot_data
        dotgraph = graph_from_dot_data(dotdata)
        dotgraph.write(filename, format=format)

    def write_tag_graph(self, root, filename, format='png'):
        graph = self.build_tag_graph(root)
        self.write_graph(graph, filename, format=format)


def cli(args, in_, out, err):
    from argparse import ArgumentParser, FileType

    def call_function(ns):
        """Calls `ns.function`, passing arguments as determined by `ns`.

        Attributes of `ns` which are listed in `ns.kw_from_ns`
          are added to the set of keyword arguments passed to `ns.function`.
        """
        kwargs = dict((key, value) for key, value in ns.__dict__.iteritems()
                                   if key in ns.kw_from_ns)
        return ns.function(**kwargs)

    def dump(ns):
        if ns.list is False:
            kw_from_ns = ['width', 'maxdepth', 'ruleset']
            kwargs = dict((key, value) for key, value in ns.__dict__.iteritems()
                                       if value)
            dumper = LXML_Dumper(**kwargs)
            from lxml.etree import parse, XPath
            root = parse(ns.infile).getroot()
            if ns.path:
                path = XPath(ns.path)
                return [dumper.dump(e) for e in path(root)]
            else:
                return dumper.dump(root)
        else:
            return LXML_Dumper.print_rulesets(ruleset=ns.list,
                                              verbose=ns.verbose)

    # Map subcommands to actions.
    # This seemed necessary because it's not possible to
    #   use set_defaults to control nested subcommands.
    # Then I discovered that you can't implement optional subcommands.
    # At this point it could be worked back into set_defaults calls,
    #   but it may be useful to use nested subcommands at a later point.
    action_map = {}

    parser = ArgumentParser()
    parser.add_argument('-i', '--infile', type=FileType, default=in_,
                        help='The XML file to learn about.\n'
                             'Defaults to stdin.')

    subparsers = parser.add_subparsers(title='subcommands', dest='action')
    p_dump = subparsers.add_parser('dump',
        help='Dump xml data according to a set of rules.',
        description='Dump xml data according to a set of rules.')
    action_map['dump'] = {'action': dump}

##--Doesn't work because it forces the use of a subcommand.
##--      p_dump_subp = p_dump.add_subparsers(title='subcommands', dest='action')
##--      p_dump_rules = p_dump_subp.add_parser('rules',
##--          help='Get information about available rules',
##--          description=LXML_Dumper.print_rulesets.__doc__)
##--      action_map['rules'] = {'action': call_function,
##--                             'function': LXML_Dumper.print_rulesets,
##--                             'kw_from_ns': ['verbose', 'ruleset']}
##--      p_dump_rules.add_argument('-v', '--verbose', action='store_true')
##--      p_dump_rules.add_argument(dest='ruleset', nargs='?',
##--                                choices=LXML_Dumper.rulesets)

    p_dump.add_argument('-l', '--list-rulesets', metavar='RULESET',
                        nargs='?', default=False, dest='list',
                        help='Get a list of rulesets '
                             'or information about a particular ruleset')
    # TODO: make the required nature of -r depend on the presence of a ruleset
    p_dump.add_argument('-r', '--ruleset',
                        choices=LXML_Dumper.rulesets.keys(),
                        default=LXML_Dumper.default_ruleset,
                        help='Which set of rules to apply.\nDefaults to "{0}".'
                             .format(LXML_Dumper.default_ruleset))
    p_dump.add_argument('-d', '--maxdepth', type=int,
                        help='How many levels to dump.')
    # TODO: set default width to console width
    p_dump.add_argument('-w', '--width', type=int,
                        help='The output width of the dump.')
    p_dump.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose ruleset list.\n'
                             'Only useful with `-l`.')

    p_dump.add_argument(dest='path', nargs='?', default=None,
                        help='The XPath to the node to be dumped.\n'
                             'Defaults to the root node.')

    namespace = parser.parse_args(args)

    # Push the action map into the namespace
    for attrib, value in action_map[namespace.action].iteritems():
        setattr(namespace, attrib, value)

    return namespace.action(namespace)


if __name__ == '__main__':
    from sys import argv, stdin, stdout, stderr
    cli(argv[1:], stdin, stdout, stderr)
