import email
import os
import django.core.exceptions as e
from django.conf import settings
from models import EmailEntry, Entry

EMAIL_ADDRESS = 'postman@%s' % settings.EMAIL_HOST


def gen_keys():
    return os.urandom(16).encode('hex')


def alloc_email_entry(user, date):
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
    name, addr = email.utils.parseaddr(string)
    return addr


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


def composite_email(headers, html=''):
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    message = MIMEMultipart('alternative')
    for key, value in headers.items():
        message.add_header(key, value)
    # add From field
    message.add_header('From', EMAIL_ADDRESS)
    # add content here
    if html:
        from bs4 import BeautifulSoup
        text = BeautifulSoup(html).get_text()
        text_part = MIMEText(text, 'plain')
        html_part = MIMEText(html, 'html')
        message.attach(html_part)
        message.attach(text_part)
    return message


def notify_email(email_entry):
    ''' generate email for notify.
        sending job is not done here, just merely composite
        return a email.message object
    '''
    def content(user):
        ''' get content of email as string'''
        from django.template.loader import render_to_string
        context = {}
        if user.setting.attach:  # user has such setting
            entrys = user.entry_set.all()
            size = len(entrys)
            if size:
                import random
                from datetime import date
                index = random.randrange(0, size)
                entry = entrys[index]
                delta = date.today() - entry.date
                context['entry'] = entry
                context['days'] = delta.days
        return render_to_string('email/notify.html', context)

    subject = 'Hi %(nickname)s, it\'s %(date)s. How is your day?' % {
        'nickname': email_entry.user.setting.nickname,
        'date': '%s %d' % (email_entry.date.strftime('%b'), email_entry.date.day),
    }
    headers = {
        'To': email_entry.user.username,
        'Message-ID': message_ID_pack(email_entry.keys),
        'Subject': subject,
    }
    return composite_email(headers, html=content(email_entry.user))
