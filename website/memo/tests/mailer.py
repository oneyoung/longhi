import email
import re
from datetime import date
from memo import mailer
from memo.models import EmailEntry, Entry
from django.test import TestCase
import utils


class MailerTest(TestCase):
    def setUp(self):
        self.user = utils.create_user()

    def tearDown(self):
        self.user.delete()

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

        message = mailer.notify_email(ee)
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
        # TODO content check
