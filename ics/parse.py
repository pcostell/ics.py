#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import
from six import PY2, PY3
from six.moves import filter, map, range

import collections
import pyparsing as pp

CRLF = '\r\n'


class ParseError(Exception):
    pass


class ContentLine:
    """ represents one property of calender content

    name:   the name of the property (uppercased for consistency and
            easier comparing)
    params: a dict of the parameters
    value:  its value
    """

    def __eq__(self, other):
        return (self.name == other.name and
                self.params == dict(other.params) and
                self.value == other.value)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __init__(self, name, params=None, value=''):
        self.name = name.upper()
        self.params = params or collections.OrderedDict()
        self.value = value

    def __str__(self):
        params_str = ''
        for pname, pvalue in self.params.items():
            params_str += ';{}={}'.format(pname, ','.join(pvalue))
        ret = "{}{}:{}".format(self.name, params_str, self.value)
        return ret.encode('utf-8') if PY2 else ret

    def __repr__(self):
        return "<ContentLine '{}' with {} parameter{}. Value='{}'>" \
            .format(
                self.name,
                len(self.params),
                "s" if len(self.params) > 1 else "",
                self.value,
            )

    def __getitem__(self, item):
        return self.params[item]

    def __setitem__(self, item, *values):
        self.params[item] = [val for val in values]

    @classmethod
    def parse(cls, line):
        if ':' not in line:
            raise ParseError("No ':' in line '{}'".format(line))

        # Separate key and value
        wordBNF = pp.Word(pp.printables + ' \n\t\r',
                          excludeChars='=;:,"')
        nameBNF = wordBNF
        multilineQuoteBNF = pp.QuotedString('"', multiline=True,
                                           escChar='\\',
                                           unquoteResults=False)
        paramValueBNF = pp.Or([multilineQuoteBNF,
                               wordBNF])
        paramBNF = pp.Group(wordBNF +
            pp.Suppress(pp.Literal('=')) +
            pp.delimitedList(paramValueBNF,
                             delim=','))
        paramsBNF = pp.Group(pp.ZeroOrMore(
            pp.Suppress(pp.Literal(';')) +
            paramBNF))
        valueBNF = pp.SkipTo(pp.StringEnd(), include=True)
        lineBNF = (pp.Optional(nameBNF +
                               paramsBNF) +
                   pp.Suppress(pp.Literal(':')) +
                   valueBNF)
        try:
            split_line = lineBNF.parseString(line, parseAll=True)
            name = ''
            params = []
            value = ''
            if len(split_line) == 1:
                value, = split_line
            elif len(split_line) == 2:
                name, value = split_line
            else:
                name, params, value = split_line
                params = [(t[0], t[1:]) for t in params]
                params = collections.OrderedDict(params)
            return cls(name, params, value.rstrip(' \n\t\r'))
        except pp.ParseException:
            raise ParseError("Unable to parse %s" % line)

    def clone(self):
        # dict(self.params) -> Make a copy of the dict
        return self.__class__(self.name,
                              collections.OrderedDict(self.params),
                              self.value)


class Container(list):
    """ represents one calendar object.
    Contains a list of ContentLines or Containers.

    name: the name of the object (VCALENDAR, VEVENT etc.)
    """

    def __init__(self, name, *items):
        super(Container, self).__init__(items)
        self.name = name

    def __str__(self):
        name = self.name
        if PY2:
            name = name.encode('utf-8')  # can self.name ever contain a non-ASCII character?
        ret = ['BEGIN:' + name]
        for line in self:
            ret.append(str(line))
        ret.append('END:' + name)
        return CRLF.join(ret)

    def __repr__(self):
        return "<Container '{}' with {} element{}>" \
            .format(self.name, len(self), "s" if len(self) > 1 else "")

    @classmethod
    def parse(cls, name, tokenized_lines):
        items = []
        for line in tokenized_lines:
            if line.name == 'BEGIN':
                items.append(Container.parse(line.value, tokenized_lines))
            elif line.name == 'END':
                if line.value != name:
                    raise ParseError(
                        "Expected END:{}, got END:{}".format(name, line.value))
                break
            else:
                items.append(line)
        return cls(name, *items)

    def clone(self):
        c = self.__class__(self.name)
        for elem in self:
            c.append(elem.clone())
        return c


def unfold_lines(physical_lines):
    if not isinstance(physical_lines, collections.Iterable):
        raise ParseError('Parameter `physical_lines` must be an iterable')
    current_line = ''
    for line in physical_lines:
        if len(line.strip()) == 0:
            continue
        elif not current_line:
            current_line = line.strip('\r')
        elif line[0] == ' ':
            # TODO : remove more spaces if needed
            current_line += line[1:].strip('\r')
        else:
            yield(current_line)
            current_line = line.strip('\r')
    if current_line:
        yield(current_line)


def tokenize_line(unfolded_lines):
    for line in unfolded_lines:
        yield ContentLine.parse(line)


def parse(tokenized_lines, block_name=None):
    res = []
    for line in tokenized_lines:
        if line.name == 'BEGIN':
            res.append(Container.parse(line.value, tokenized_lines))
        else:
            res.append(line)
    return res


def lines_to_container(lines):
    return parse(tokenize_line(unfold_lines(lines)))


def string_to_container(txt):
    return lines_to_container(txt.splitlines())

if __name__ == "__main__":
    from tests.fixture import cal1

    def print_tree(elem, lvl=0):
        if isinstance(elem, list) or isinstance(elem, Container):
            if isinstance(elem, Container):
                print("{}{}".format('   ' * lvl, elem.name))
            for sub_elem in elem:
                print_tree(sub_elem, lvl + 1)
        elif isinstance(elem, ContentLine):
            print("{}{}{}".format('   ' * lvl,
                  elem.name, elem.params, elem.value))
        else:
            print('Wuuut?')

    cal = string_to_container(cal1)
    print_tree(cal)
