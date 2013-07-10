import re
import email
from models import EmailEntry, Entry


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


def handle_replied_email(mail):
    def get_reply_message(message):
        return message

    msg = email.message_from_string(mail)
    username = get_email_addr(msg.get('From'))
    keys = msg.get('In-Reply-To')
    ee = EmailEntry.objects.get(keys=keys)
    if username != ee.user.username:
        # email address not match, just return
        return
    entry = Entry(user=ee.user, date=ee.date)
    entry.text = get_reply_message(msg)
    entry.save()  # save entry
    ee.delete()  # delete email entry once we had handled
