import os.path
from datetime import date, timedelta
from memo.models import User, Entry, Statics, Setting
from django.test import TestCase
from django.core import exceptions

FILES_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'files')


def create_user():
    user = 'test@test.com'
    pswd = 'usertest'
    user = User.objects.create_user(username=user, password=pswd)
    user.save()
    return user


class UserTest(TestCase):
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
        # can access Entry set
        user.entry_set.all()

        # after user delete, these should all gone
        user.delete()
        with self.assertRaises(exceptions.ObjectDoesNotExist):
            Statics.objects.get(pk=statics_pk)
        with self.assertRaises(exceptions.ObjectDoesNotExist):
            Setting.objects.get(pk=setting_pk)


class EntryTest(TestCase):
    def setUp(self):
        self.user = create_user()

    def tearDown(self):
        self.user.delete()

    def test_save_and_read(self):
        user = self.user

        # load our markdown test sample from files
        import codecs
        text = codecs.open(os.path.join(FILES_DIR, 'markdown-documentation-basics.txt'),
                           'r', encoding='utf8').read()
        html = codecs.open(os.path.join(FILES_DIR, 'markdown-documentation-basics.html'),
                           'r', encoding='utf8').read()
        entry_date = date.today()
        # save, should not cause any exception
        entry = Entry()
        entry.date = entry_date
        entry.text = text
        entry.user = user
        entry.save()

        # we can query entry from user
        entry = user.entry_set.get(date=entry_date)
        # markdown test, after save, html should translated by markdown
        # save file for later diff compare
        fd = codecs.open('/tmp/html', 'w', encoding='utf8')
        fd.write(entry.html)
        fd.close()
        self.assertEquals(entry.html, html)
        # after save, text should be the same
        self.assertEquals(entry.text, text)


class StaticsTest(TestCase):
    def setUp(self):
        self.user = create_user()

    def tearDown(self):
        self.user.delete()

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
            entry = Entry()
            entry.date = entry_date
            entry.text = 'text'
            entry.user = user
            entry.save()
            return entry

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
