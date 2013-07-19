from datetime import date, timedelta
from memo.models import User, Statics, Setting, EmailEntry
from memo.mailer import alloc_email_entry
from django.test import TestCase
from django.core import exceptions
from . import utils


class BaseTest(TestCase):
    def setUp(self):
        self.user = utils.create_user()

    def tearDown(self):
        self.user.delete()


class UserTest(BaseTest):
    def test_user_fileds_access(self):
        user = 'usertest@test.com'
        pswd = 'usertest'
        user = User.objects.create_user(username=user, password=pswd)
        user.save()

        # can get the new user
        user = User.objects.get(username=user)
        # can access Statics
        statics_pk = user.statics.pk
        self.assertIsInstance(user.statics, Statics)
        # can access Setting
        setting_pk = user.setting.pk
        self.assertIsInstance(user.setting, Setting)
        self.assertTrue(user.setting.keys)  # keys should not null
        # can access Entry set
        user.entry_set.all()

        # after user delete, these should all gone
        user.delete()
        with self.assertRaises(exceptions.ObjectDoesNotExist):
            Statics.objects.get(pk=statics_pk)
        with self.assertRaises(exceptions.ObjectDoesNotExist):
            Setting.objects.get(pk=setting_pk)


class EntryTest(BaseTest):
    def test_save_and_read(self):
        user = self.user

        # load our markdown test sample from files
        import codecs
        text = utils.read_file('markdown-documentation-basics.txt')
        html = utils.read_file('markdown-documentation-basics.html')

        def create_entry(entry_date, text, html):
            # create, should not cause any exception
            utils.create_entry(date=entry_date, user=user, text=text)

            # we can query entry from user
            entry = user.entry_set.get(date=entry_date)
            # check html output
            # save file for later diff compare
            fd = codecs.open('/tmp/html', 'w', encoding='utf8')
            fd.write(entry.html)
            fd.close()
            self.assertEquals(entry.html, html)
            # after save, text should be the same
            self.assertEquals(entry.text, text)

        entry_date = date.today()
        # by default, markdown is not enabled
        # so when convert to html, it will add <p> tag
        create_entry(entry_date, 'pppp', '<p>pppp</p>')

        # turn on markdown trigger
        user.setting.markdown = True
        user.setting.save()
        entry_date = date.today() + timedelta(1)
        create_entry(entry_date, text, html)


class StaticsTest(BaseTest):
    def test_count_store(self):
        user = self.user

        def statics_equal(entrys, streak, record):
            statics = self.user.statics  # get a fresh data
            self.assertEqual(entrys, statics.entrys)
            self.assertEqual(streak, statics.streak)
            self.assertEqual(record, statics.record)

        # for a new user, all count should be zero
        statics_equal(0, 0, 0)

        # let's create some entrys in a fews dayo
        def create_entry(entry_date):
            return utils.create_entry(date=entry_date, user=user, text='text')

        step = user.setting.interval  # get user set notify interval
        start_date = date.today()
        for i in range(4):  # create 4 entry
            start_date += timedelta(step)
            create_entry(start_date)
        statics_equal(4, 4, 4)

        # let's skip a time, streak is clear
        start_date += timedelta(step * 2)
        create_entry(start_date)
        statics_equal(5, 0, 4)

        # why not create a new record
        for i in range(10):
            start_date += timedelta(step)
            create_entry(start_date)
        statics_equal(15, 10, 10)


class EmailEntryTest(BaseTest):
    def test_emailentry(self):
        user = self.user
        today = date.today()
        # unique test
        keys = '1234556789'
        e1 = EmailEntry(user=user, date=today, keys=keys)
        e1.save()
        # the same keys should raise excpetion
        e2 = EmailEntry(user=user, date=today, keys=keys)
        with self.assertRaises(Exception):
            e2.save()

        # test utils.alloc_email_entry
        for i in range(10):
            alloc_email_entry(user, today)


class SettingModelTest(TestCase):
    def setUp(self):
        self.user = utils.create_user()

    def tearDown(self):
        self.user.delete()

    def test_utc_offset(self):
        s = self.user.setting

        # setting timezone
        s.timezone = '8.0'
        s.preferhour = 0
        s.interval = 1
        self.assertEqual(s.utc_offset(), timedelta(hours=8))

        s.interval = 2
        self.assertEqual(s.utc_offset(), timedelta(hours=32))

        s.timezone = '9.0'
        self.assertEqual(s.utc_offset(), timedelta(hours=33))

        s.preferhour = 8
        self.assertEqual(s.utc_offset(), timedelta(hours=41))
