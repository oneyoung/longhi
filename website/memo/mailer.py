import email
from django.conf import settings
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from .models import EmailEntry, Entry
from . import utils

EMAIL_ADDRESS = 'postman@%s' % settings.EMAIL_HOST


def alloc_email_entry(user, date):
    ee = EmailEntry(user=user, date=date)
    utils.alloc_keys(ee, 'keys')
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
    ''' composite and return Django email object '''
    from django.core.mail import EmailMultiAlternatives
    from bs4 import BeautifulSoup

    subject = headers.pop('Subject')
    to = headers.pop('To')

    text = BeautifulSoup(html).get_text()

    msg = EmailMultiAlternatives(subject, text, EMAIL_ADDRESS, [to], headers=headers)
    msg.attach_alternative(html, 'text/html')
    return msg


def notify_email(email_entry):
    ''' generate email for notify.
        sending job is not done here, just merely composite
    '''
    def content(user):
        ''' get content of email as string'''
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


def activate_email(user):
    ''' generate email for user email activation.
    '''
    # header
    subject = 'Hi %s, activate your account.' % user.setting.nickname
    headers = {
        'To': user.username,
        'Subject': subject,
    }

    # content
    url = utils.fullurl(reverse('memo.views.activate',
                                kwargs={'keys': user.setting.keys}))
    context = {
        'nickname': user.setting.nickname,
        'link': url,
    }
    content = render_to_string('email/activate.html', context)

    return composite_email(headers, html=content)
