"""Routines to parse mpd's protocol documentation."""

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
