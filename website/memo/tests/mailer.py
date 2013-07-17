import email
import re
import os
from bs4 import BeautifulSoup
from datetime import date
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from memo import mailer
from memo.models import EmailEntry, Entry
from memo.utils import get_settings
import utils


def get_html(mail):
    for part in mail.walk():
        if part.get_content_type() == 'text/html':
            return part.get_payload()


@override_settings(EMAIL_BACKEND='django.core.mail.backends.filebased.EmailBackend',
                   EMAIL_FILE_PATH='/tmp/memo-message')
class MailBase(TestCase):
    def setUp(self):
        # setup inbox dir
        self.inbox_dir = get_settings('EMAIL_FILE_PATH')
        os.system('mkdir -p %s' % self.inbox_dir)
        self.user = utils.create_user()

    def tearDown(self):
        self.user.delete()
        # clear inbox_dir
        os.system('rm -rf %s' % self.inbox_dir)

    def inbox(self):
        ''' return a list of mails in inbox_dir '''
        mails = []
        for fname in os.listdir(self.inbox_dir):
            path = os.path.join(self.inbox_dir, fname)
            if os.path.isfile(path):
                mail = email.message_from_file(open(path))
                mails.append(mail)
        return mails

    def clear_inbox(self):
        os.system('rm -rf %s/*' % self.inbox_dir)

    def recv_mail(self, user):
        ''' fetch user specified email '''
        mails = []
        for m in self.inbox():
            if m.get('To') == user.username:
                mails.append(m)
        return mails


class MailerTest(MailBase):
    def test_send_activate_email_when_user_register(self):
        # after user created, a and only one email should sent
        inbox = self.recv_mail(self.user)
        self.assertEqual(len(inbox), 1)
        # mail content check
        mail = inbox[0]
        html = get_html(mail)
        soup = BeautifulSoup(html)
        a = soup.find(id='activate')
        self.assertIn(reverse('memo.views.activate',
                              kwargs={'keys': self.user.setting.keys}), a['href'])

    def test_handle_reply_message(self):
        email_text = utils.read_file('replied-email.txt')
        msg = email.message_from_string(email_text)
        today = date.today()
        keys = mailer.message_ID_extract(msg.get('In-Reply-To'))

        # let's create a entry here
        ee = EmailEntry(user=self.user, date=today)
        ee.keys = keys
        ee.save()

        # test begin
        mailer.handle_replied_email(email_text)
        # email entry should gone after handled
        self.assertFalse(EmailEntry.objects.filter(keys=keys).exists())
        # we could get the entry of specified date
        entry = Entry.objects.get(user=self.user, date=today)
        # check the text
        self.assertEquals(entry.text, 'Reply to this email\n')

    def test_messageID(self):
        keys = "aksdfjalsdkfjaslkdf"
        # pack test
        msgid = mailer.message_ID_pack(keys)
        # format message-id = "<" local-part "@" domain ">"
        self.assertTrue(re.match("<\S+@\S+>", msgid))

        # unpack test
        keys2 = mailer.message_ID_extract(msgid)
        self.assertEquals(keys, keys2)

    def test_notify_email(self):
        nickname = "dummynick"
        self.user.setting.nickname = nickname
        d = date(2013, 6, 9)
        ee = mailer.alloc_email_entry(self.user, d)

        message = mailer.notify_email(ee).message()
        # message is a email.message object, let's exam the result
        # * should contain the message ID
        self.assertIn(ee.keys, message.get('Message-ID'))
        # * should send to the user
        self.assertEquals(ee.user.username, message.get('To'))
        # should have the from
        self.assertTrue(message.get('From'))
        # Subject check
        subject = message.get('Subject')
        self.assertIn('Hi %s' % nickname, subject)  # have nickname
        self.assertIn('Jun 9', subject)  # have date, and should strip heading 0
        # content check
        self.assertIn('Just reply', message.as_string())

        # attach test
        self.user.setting.attach = True
        self.user.setting.save()
        text = "Entry tesst haha"
        utils.create_entry(d, self.user, text=text)
        message = mailer.notify_email(ee).message()
        self.assertIn(text, message.as_string())

    def test_activate_email(self):
        nickname = "dummynick"
        self.user.setting.nickname = nickname
        self.user.setting.save()

        message = mailer.activate_email(self.user).message()
        # subject check
        self.assertIn(nickname, message.get('Subject'))
        # content check
        html = get_html(message)
        soup = BeautifulSoup(html)
        a = soup.find(id="activate")
        url = a['href']
        # url should equal to text, in case url was banned
        self.assertEquals(url, a.text)
        self.assertIn(reverse('memo.views.activate',
                              kwargs={'keys': self.user.setting.keys}), url)
