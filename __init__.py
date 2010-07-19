#!/usr/bin/env python
"""Library and CLI for learning about XML formats."""

from lxml import etree

class Dumper(object):
    """Dump an lxml.etree tree starting at `element`.
    
    Attributes:
        maxdepth: the maximum recursion level.
        width: the width at which text will be wrapped.
        ruleset: either a string matching one of the keys of rulesets,
                 or a Mapping containing such a ruleset.
        outstream: a stream to which the dump will be written.

    For now, this function is just useful for sussing out the shape of the XML.
    """
    # TODO: write doctest examples

    # Each ruleset maps tags to kwargs for `format_element`.
    rulesets = {'full': {None: {'recurse': True}}}

    default_ruleset = 'full'

    from sys import stdout
    outstream = stdout
        
    from pprint import PrettyPrinter
    pformat = PrettyPrinter(indent=2).pformat

    # Some more defaults.
    maxdepth = None
    width = 80

    # This should maybe be moved into the CLI.
    @classmethod
    def print_rulesets(cls, ruleset=None, outstream=None,
                            format=pformat, verbose=False):
        """Output ruleset information.

        If a `ruleset` is given, that ruleset's rules are output.
        If no `ruleset` is given, a list of rulesets is output.
        
        The `verbose` option will cause full ruleset information
          to be given in the list of rulesets.

        `format` can be used to specify a different formatting function.
        """

        outstream = outstream if outstream else cls.outstream

        if ruleset:
            outstream.write(format(cls.rulesets[ruleset]))
        else:
            if verbose:
                outstream.write(format(cls.rulesets))
            else:
                outstream.writelines("\n".join(cls.rulesets.keys()))
        outstream.write("\n")


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

    def dump(self, element, **kwargs):
        """Dump `element` according to `ruleset`.
        
        Keyword arguments:
            depth: the initial depth of the dump.  Normally this will be 0.

            Additionally, the `outstream`, `maxdepth`, and `ruleset`
              object attributes can be overridden without modifying the object.

            If `ruleset` is not given, `self`'s default ruleset is used.

        I suspect that actually using XSLT would be a better way to do this.
        """
        from copy import copy
        from collections import Mapping

        depth = kwargs.pop('depth', 0)
        # Pull variables from kwargs or self
        maxdepth, outstream = (kwargs.pop(v, getattr(self, v))
                               for v in ('maxdepth', 'outstream'))

        ruleset = kwargs.pop('ruleset', getattr(self, 'ruleset',
                                                self.default_ruleset))

        if isinstance(ruleset, basestring):
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
            outstream.write(self.format_element(element, depth, **kwargs))
            outstream.write("\n")
            if recurse:
                if maxdepth is None or maxdepth > depth:
                    for child in element.getchildren():
                        _dump(child, depth + 1)

        _dump(element, depth=depth)


def iter_unique_child_tags(bases, tags):
    """Iterates through unique child tags for combinations of
        `bases` and `tags`.

    `bases` and `tags` can be singular -- elements and strings --
      or iterables of those respective types.
    """
    # both elements and strings are iterable types,
    #   so we need to check for those specific types.
    bases, tags = (iter((param,)) if isinstance(param, type) else iter(param)
                   for (param, type) in ((bases, etree._Element),
                                         (tags, basestring)))

    from itertools import chain
    tag_nodes = (node for base in bases for tag in tags
                      for node in base.iter(tag))

    child_tags = (child.tag for node in tag_nodes
                            for child in node.getchildren())

    found_child_tags = set()
    for tag in child_tags:
        if tag not in found_child_tags:
            found_child_tags.add(tag)
            yield tag

def iter_tag_list(bases):
    """List all unique tags at and under the `root` node.

    `bases` can be a single element or an iterable of them.
    """
    bases = (iter((bases,)) if isinstance(bases, etree._Element)
                            else iter(bases))

    from itertools import chain

    tags = (node.tag for base in bases
                     for node in base.iter()
                     if hasattr(node, 'tag'))
    found_tags = set()
    for t in tags:
        if t not in found_tags:
            found_tags.add(t)
            yield t

def build_tag_graph(bases):
    """Build a python-graph graph of the tag relationships.
    
    `bases` is an element or iterable of elements.
    """
    from pygraph.classes.digraph import digraph

    g = digraph()

    tags = list(iter_tag_list(bases))
    g.add_nodes(tags)

    # TODO: this is totally inefficient:
    #         it makes more sense to do each base separately,
    #         to avoid searching it for tags it doesn't have.
    #       The better way is to build the set of all bases' edges.
    for tag in tags:
        for child in iter_unique_child_tags(bases, tag):
            g.add_edge((tag, child))

    return g

def write_graph(graph, filename, format='svg'):
    """Write a python-graph graph as an image.

    `format` can be any of those supported by pydot.Dot.write().
    """
    from pygraph.readwrite.dot import write
    dotdata = write(graph)

    from pydot import graph_from_dot_data
    dotgraph = graph_from_dot_data(dotdata)
    dotgraph.write(filename, format=format)

def write_tag_graph(bases, filename, format='png'):
    """Build and write a graph of the tag relationships in `bases`.

    `bases` can be a single element or an iterable of them.
    """
    graph = build_tag_graph(bases)
    write_graph(graph, filename, format=format)


# TODO: refactor this as a class.
def cli(args, in_, out, err, Dumper=Dumper):
    """Provide a command-line interface to the module functionality.

    Dumper: xmlearn.Dumper or subclass.
            Called in response to the `dump` subcommand.
            Note that this should be the *class*, not an instantiation of it.

    args: the arguments to be parsed.

    in_, out, err: open input/output/error files.
    """

    from argparse import ArgumentParser, FileType, Action

    def instantiate_dumper(ns):
        kw_from_ns = ['width', 'maxdepth', 'ruleset', 'outstream']
        kwargs = dict((key, value) for key, value in ns.__dict__.iteritems()
                                    if key in kw_from_ns and value is not None)
        return Dumper(**kwargs)

    def dump(ns):
        """Initializes a Dumper with values from the namespace `ns`.

        False values are filtered out.
        Dumps `ns.path` from the XML file `ns.infile`.
        """
        dumper = instantiate_dumper(ns)
        root = etree.parse(ns.infile).getroot()
        return [dumper.dump(e) for e in ns.path(root)]

    def list_rulesets(ns):
        return Dumper.print_rulesets(ruleset=ns.ruleset,
                                     verbose=ns.verbose)
        

    parser = ArgumentParser()
    parser.add_argument('-i', '--infile', type=FileType, default=in_,
                        help='The XML file to learn about.\n'
                             'Defaults to stdin.')
    parser.add_argument('-p', '--path', default='/*', type=etree.XPath,
                        help='An XPath to be applied to various actions.\n'
                             'Defaults to the root node.')

    subparsers = parser.add_subparsers(title='subcommands')

    def build_dump_parser(subparsers):
        p_dump = subparsers.add_parser('dump',
            help='Dump xml data according to a set of rules.',
            description='Dump xml data according to a set of rules.')

        p_dump.set_defaults(action=dump, outstream=out)

        class ListRulesetsAction(Action):
            def __call__(self, parser, namespace, values, option_string=None):
                setattr(namespace, 'action', list_rulesets)
                setattr(namespace, 'ruleset', values)
        p_dump.add_argument('-l', '--list-rulesets', metavar='RULESET',
                            nargs='?', action=ListRulesetsAction,
                            help='Get a list of rulesets '
                                'or information about a particular ruleset')

        p_dump.add_argument('-r', '--ruleset',
                            choices=Dumper.rulesets.keys(),
                            default=Dumper.default_ruleset,
                            help='Which set of rules to apply.\n'
                                 'Defaults to "{0}".'
                                .format(Dumper.default_ruleset))

        p_dump.add_argument('-d', '--maxdepth', type=int,
                            help='How many levels to dump.')
        # TODO: set default width to console width
        # TODO: also apply the console width to the help display
        p_dump.add_argument('-w', '--width', type=int,
                            help='The output width of the dump.')
        p_dump.add_argument('-v', '--verbose', action='store_true',
                            help='Enable verbose ruleset list.\n'
                                'Only useful with `-l`.')
    build_dump_parser(subparsers)


    def build_tags_parser(subparsers):
        p_list = subparsers.add_parser('tags',
            help='Show information about tags.',
            description='Show information about tags.')

        def taglist(ns):
            root = etree.parse(ns.infile).getroot()
            itemfmt = '    {item}\n' if ns.show_element else '{item}\n'
            elements = ns.path(root)
            if ns.combine:
                elements = (elements,)
                eltfmt = lambda e: '[multiple elements]\n'
            else:
                eltfmt = lambda e: e.getroottree().getpath(e) + "\n"
            for element in elements:
                if ns.show_element:
                    out.write(eltfmt(element))
                for item in ns.tagfunc(element, *ns.tagfunc_args):
                    out.write(itemfmt.format(item=item))

        p_list.set_defaults(action=taglist,
                            tagfunc=iter_tag_list, tagfunc_args=[])

        p_list.add_argument('-e', '--show-element', action='store_true',
            help='Enables display of the element path.\n'
                 'Without this option, data from multiple matching elements '
                 'will be listed in unbroken series.\n'
                 'This is mostly useful '
                 'when the path selects multiple elements.')
        p_list.add_argument('-C', '--no-combine', action='store_false',
                            dest='combine',
                            help='Do not combine results '
                                 'from various path elements.\n'
                                 'This option is only meaningful '
                                 'when the --path leads to multiple elements.')

        class ListChildrenAction(Action):
            """Change the tag function and set the extra argument."""
            def __call__(self, parser, namespace, values, option_string=None):
                if values:
                    setattr(namespace, 'tagfunc', iter_unique_child_tags)
                    setattr(namespace, 'tagfunc_args', [values])
        p_list.add_argument('-c', '--child', nargs='?', metavar='PARENT',
            action=ListChildrenAction,
            help='List all tags which appear as children of PARENT.')
    build_tags_parser(subparsers)

    def build_graph_parser(subparsers):
        try:
            from pydot import Dot
            formats = Dot().formats
        except ImportError:
            return

        p_graph = subparsers.add_parser('graph',
            help='Build a graph from the XML tags relationships.',
            description='Build a graph from the XML tags relationships.')

        def act(ns):
            extension = ns.outfile.split('.')[-1]
            if ns.format:
                if extension != ns.format:
                    ns.outfile += '.' + ns.format
            else:
                if extension in formats:
                    ns.format = extension

            root = etree.parse(ns.infile).getroot()
            write_tag_graph(ns.path(root), ns.outfile, ns.format)

        p_graph.set_defaults(action=act)
        p_graph.add_argument('--format', choices=formats, metavar='FORMAT',
                             help='The format for the graph image.\n'
                                  'It will be appended to the filename '
                                  'unless they already concur '
                                  'or -F is passed.\n'
                                  'Choose from ' + str(formats))
        p_graph.add_argument('-F', '--force-extension',
                             help='Allow the filename extension to differ '
                                  'from the file format.\n'
                                  'Without this option, the format extension '
                                  'will be appended to the filename.')
        p_graph.add_argument(dest='outfile', default=None,
                             help='The filename for the graph image.\n'
                                  'If no --format is given, '
                                  'it will be based on this name.')
    build_graph_parser(subparsers)

    namespace = parser.parse_args(args)

    return namespace.action(namespace)


if __name__ == '__main__':
    from sys import argv, stdin, stdout, stderr
    cli(argv[1:], stdin, stdout, stderr)
