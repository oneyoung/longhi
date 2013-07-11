import re
import email
import os
import django.core.exceptions as e
from django.conf import settings
from models import EmailEntry, Entry


def gen_keys():
    return os.urandom(16).encode('hex')


def alloc_email_entry(user, date):
    from models import EmailEntry
    ee = EmailEntry(user=user, date=date)
    while 1:
        ee.keys = gen_keys()
        try:
            ee.validate_unique()
            break
        except e.ValidationError:
            continue
    ee.save()
    return ee


def get_email_addr(string):
    '''extract email address from From head.

    >>> get_email_addr('xxx@xxx.com')
    'xxx@xxx.com'
    >>> get_email_addr('XXX <xxx@xxx.com>')
    'xxx@xxx.com'
    '''
    regexp = re.compile('(.*<)?(?P<email>.+@\S+\.\w+)>?')
    m = regexp.match(string)
    if m:
        return m.group('email')


def message_ID_pack(keys):
    ''' message-id = "<" local-part "@" domain ">" '''
    domain = settings.EMAIL_HOST
    return "<%s@%s>" % (keys, domain)


def message_ID_extract(msgid):
    ''' message id unpack '''
    return msgid.split('@')[0].strip('<')


def handle_replied_email(mail):
    def get_reply_message(message):
        from email_reply_parser import EmailReplyParser

        for payload in message.get_payload():
            if payload.get_content_type() == 'text/plain':
                content = payload.get_payload()
                break

        return EmailReplyParser.parse_reply(content)

    msg = email.message_from_string(mail)
    username = get_email_addr(msg.get('From'))
    keys = message_ID_extract(msg.get('In-Reply-To'))
    ee = EmailEntry.objects.get(keys=keys)
    if username != ee.user.username:
        # email address not match, just return
        return
    entry = Entry(user=ee.user, date=ee.date)
    entry.text = get_reply_message(msg)
    entry.save()  # save entry
    ee.delete()  # delete email entry once we had handled


def notify_email(email_entry):
    ''' generate email for notify.
        sending job is not done here, just merely composite
        return a email.message object
    '''
    pass
