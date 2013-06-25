import datetime


def str2entrys(string):
    import re

    eol = '\n'  # end of line pattern
    regstr = str('^(?P<date>\d{4}-\d{2}-\d{2})' +  # match 'YYYY-MM-DD
                 '(?P<star>( \*)?)$%s' % eol +  # match a optional star mark
                 eol +  # match a new line
                 '(?P<text>.*)')  # match the text
    result = []
    regexp = re.compile(regstr, re.M | re.S)

    def extract_entry(string):
        ' recursion to find each entry '
        for m in regexp.finditer(string):  # get only one match
            date = datetime.datetime.strptime(m.group('date'), '%Y-%m-%d').date()
            # here substr might contatin more than one entry
            substr = m.group('text')
            star = m.group('star').strip() == '*'
            # get the current text by remove next match
            text = regexp.sub('', substr)[:-1]  # need remove last '\n' char
            result.append((date, text, star))
            # continue to find next one
            extract_entry(substr)

    extract_entry(string)
    return result
