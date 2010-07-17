"""Routines to parse mpd's protocol documentation."""
from pprint import PrettyPrinter as _PrettyPrinter

from xml.etree import ElementTree as _ElementTree

class TagsPrinter(_PrettyPrinter):
    """Prettyprint tags from etree elements.
    
    This doesn't really work very well."""

    from pprint import _recursion, _safe_repr, _commajoin
    _recursion = staticmethod(_recursion)
    _safe_repr = staticmethod(_safe_repr)
    _commajoin = staticmethod(_commajoin)

    def format(self, object, context, maxlevels, level):
        if isinstance(object, _ElementTree._ElementInterface):
            return self._format_element(object, context,
                                        maxlevels, level)
        else:
            return self._safe_repr(object, context, maxlevels, level)

    def _format_element(self, object, context, maxlevels, level):
        """Handle formatting of ElementTree._ElementInterface objects."""
        # This code is based on the case of pprint._safe_repr
        #   which handles list and tuple instances.
        tag = object.tag
        if len(object) == 1:
            format = tag + ': (%s,)'
        else:
            if len(object) == 0:
                return tag, False, False
            format = tag + ': (%s)'
        objid = id(object)
        if maxlevels and level >= maxlevels:
            return format % "...", False, objid in context
        if objid in context:
            return self._recursion(object), False, True
        context[objid] = 1
        readable = False
        recursive = False
        components = []
        append = components.append
        level += 1
        for o in object:
            orepr, oreadable, orecur = self.format(o, context, maxlevels,
                                                   level)
            append(orepr)
            if not oreadable:
                readable = False
            if orecur:
                recursive = True
        del context[objid]
        return format % self._commajoin(components), readable, recursive

class CommandReflection(_ElementTree.ElementTree):
    """Provides command info based on the contents of a protocol.xml file."""
    def __init__(self, source):
        _ElementTree.ElementTree.__init__(self, None, source)

    def dump_commands(self):
        return TagsPrinter().pformat(self.getroot())


# A new approach.  This seems to be working better.
class LXML_Dumper(object):
    """Dump an lxml.etree tree starting at `element`.
    
    Attributes:
        maxdepth: the maximum recursion level.
        width: the width at which text will be wrapped.
    """

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def relwrap(self, *args, **kwargs):
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

    # Each ruleset maps tags to kwargs for `format_element`.
    rulesets = {'book': {'section': {'with_text': False},
                         'para': {'linebreak': True},
                         None: {'recurse': True}},
                'full': {None: {'recurse': True}}}

    def dump(self, element, rules=rulesets['book'], depth=0):
        """Dump `element` according to `rules`.
        
        Keyword arguments:
            rules: either a string matching one of the keys of rulesets,
                     or a Mapping containing such a ruleset.
            depth: the initial depth of the dump.
        """
        from copy import copy
        from collections import Mapping

        if isinstance(rules, Mapping):
            pass
        elif isinstance(rules, basestring):
            rules = self.rulesets[rules]
        assert isinstance(rules, Mapping)

        def _dump(element, depth=0):
            for rule in rules.iteritems():
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
                if (hasattr(self, 'maxdepth') and self.maxdepth >= depth
                    or not hasattr(self, 'maxdepth')
                ):
                    for child in element.getchildren():
                        _dump(child, depth + 1)

        _dump(element, depth=depth)
                    
##--              if element.tag == 'section':
##--                  print self.format_element(element, depth, with_text=False)
##--              elif element.tag == 'para':
##--                  print self.format_element(element, depth, linebreak=True)
##--              else:
##--                  print self.format_element(element, depth)
##--                  for child in element.getchildren():
##--                      _dump(child, depth + 1)



if __name__ == '__main__':
    from sys import argv
    with open(argv[1], 'r') as f:
        print CommandReflection(f).dump_commands()
