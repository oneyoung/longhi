import os.path
from datetime import date
from memo.models import User, Entry, Statics, Setting
from django.test import TestCase
from django.core import exceptions

FILES_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'files')


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
    def test_save_and_read(self):
        # preconfig for our test
        user = 'entrytest@test.com'
        pswd = 'usertest'
        user = User.objects.create_user(username=user, password=pswd)
        user.save()

        # load our markdown test sample from files
        text = open(os.path.join(FILES_DIR, 'markdown-documentation-basics.txt')).read()
        html = open(os.path.join(FILES_DIR, 'markdown-documentation-basics.html')).read()
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
        self.assertEquals(entry.html, html)
        # after save, text should be the same
        self.assertEquals(entry.text, text)
