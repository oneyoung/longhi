import datetime
import os
import django.core.exceptions as e
from django.conf import settings


def str2date(string):
    return datetime.datetime.strptime(string, '%Y-%m-%d').date()


def date2str(date):
    return date.strftime('%Y-%m-%d')


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
            date = str2date(m.group('date'))
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


def entry2str(entry):
    return '%(date)s%(star)s\n\n%(text)s\n' % {
        'date': date2str(entry.date),
        'star': ' *' if entry.star else '',
        'text': entry.text,
    }


def gen_keys():
    return os.urandom(16).encode('hex')


def alloc_keys(model, attr):
    ''' a shortcut to alloc unique keys
    paras:
        model -- a model.Model instance
        attr -- attribute name for keys
    return:
        instance of model
    '''
    while 1:
        setattr(model, attr, gen_keys())
        try:
            model.validate_unique()
            break
        except e.ValidationError:
            print "validator error"
            continue
    return model


def fullurl(url):
    ''' return a fullurl for outside the side access '''
    if settings.DEBUG:  # debug mode
        host = "localhost:8080"
    if settings.TEST:  # test mode
        host = "localhost:8081"
    else:
        host = settings.HOST

    return ''.join(['http://', host, url])
