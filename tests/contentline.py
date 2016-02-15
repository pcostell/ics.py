import itertools
import unittest
from collections import OrderedDict
from ics.parse import ParseError, ContentLine


class TestContentLine(unittest.TestCase):

    dataset = {
        'HAHA:': ContentLine('haha'),
        ':hoho': ContentLine('', {}, 'hoho'),
        'HAHA:hoho': ContentLine('haha', {}, 'hoho'),
        'HAHA:hoho:hihi': ContentLine('haha', {}, 'hoho:hihi'),
        'HAHA;hoho=1:hoho': ContentLine('haha', {'hoho': ['1']}, 'hoho'),
        'RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU':
        ContentLine(
            'RRULE',
            {},
            'FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU'
        ),
        'SUMMARY:dfqsdfjqkshflqsjdfhqs fqsfhlqs dfkqsldfkqsdfqsfqsfqsfs':
        ContentLine(
            'SUMMARY',
            {},
            'dfqsdfjqkshflqsjdfhqs fqsfhlqs dfkqsldfkqsdfqsfqsfqsfs'
        ),
        'ATTENDEE;CUTYPE=INDIVIDUAL;X-RESPONSE-COMMENT="asd asd\n asd":value':
        ContentLine(
            'ATTENDEE',
            OrderedDict([('CUTYPE', ['INDIVIDUAL']),
                         ('X-RESPONSE-COMMENT', ['"asd asd\n asd"'])]),
            'value'
        ),
        'ATTENDEE;CUTYPE=INDIVIDUAL;NAME=O\'Shanassey:value':
        ContentLine(
            'ATTENDEE',
            OrderedDict([('CUTYPE', ['INDIVIDUAL']),
                         ('NAME', ['O\'Shanassey'])]),
            'value'
        ),
        'DTSTART;TZID=Europe/Brussels:20131029T103000':
        ContentLine(
            'DTSTART',
            {'TZID': ['Europe/Brussels']},
            '20131029T103000'
        ),
    }

    # Items in parse_dataset can be parsed but are not reversible.
    parse_dataset = {
        'BEGIN:VCALENDAR\n' :
        ContentLine('BEGIN', {}, 'VCALENDAR'),
        'haha;p2=v2;p1=v1:':
        ContentLine(
            'haha',
            OrderedDict([('p1', ['v1']), ('p2', ['v2'])]),
            ''
        ),
        'haha;hihi=p3,p4,p5;hoho=p1,p2:blabla:blublu':
        ContentLine(
            'haha',
            OrderedDict([('hihi', ['p3', 'p4', 'p5']),
                         ('hoho', ['p1', 'p2'])]),
            'blabla:blublu'
        ),
    }

    def test_errors(self):
        self.assertRaises(ParseError, ContentLine.parse, 'haha;p1=v1')
        self.assertRaises(ParseError, ContentLine.parse, 'haha;p1:')

    def test_str(self):
        for expected, actual in self.dataset.items():
            self.assertEqual(expected, str(actual))

    def test_parse(self):
        for test, expected in itertools.chain(self.dataset.items(),
                                              self.parse_dataset.items()):
            got = ContentLine.parse(test)
            self.assertEqual(expected, got)

