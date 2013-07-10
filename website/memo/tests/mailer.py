import email
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
        keys = msg.get('In-Reply-To')

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
