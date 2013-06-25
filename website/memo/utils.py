import collections
import datetime


TEntry = collections.namedtuple('TEntry', ['date', 'text', 'star'])


def str2entrys(string):
    import re

    regstr = str('^(?P<date>\d{4}-\d{2}-\d{2})' +  # match 'YYYY-MM-DD
                 '(?P<star>( \*)?)$' +  # match a optional star mark
                 '^$' +  # match a new line
                 '(?P<text>.*)' +  # match the text
                 '^$')  # tail end line
    result = []
    regexp = re.compile(regstr, re.M | re.S)
    for entry in regexp.split(string):
        m = regexp.match(entry)
        date = datetime.datetime.strptime(m.group('date'), '%Y-%m-%d').date()
        text = m.group('text')
        star = m.group('star').strip() == '*'
        result.append((date, text, star))
    return result
