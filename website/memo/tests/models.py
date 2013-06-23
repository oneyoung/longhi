from memo.models import User, Entry, Statics, Setting
from django.test import TestCase


class UserTest(TestCase):
    def test_user_fileds_access(self):
        user = 'usertest@test.com'
        pswd = 'usertest'
        user = User.objects.create_user(username=user, password=pswd)
        user.save()

        # can get the new user
        user = User.objects.get(username=user)
        # can access Statics
        self.assertIsInstance(user.statics, Statics)
        # can access Setting
        self.assertIsInstance(user.setting, Setting)
        # can access Entry
        user.entry_set.objects.all()


class EntryTest(TestCase):
    def test_save_and_read(self):
        # save, should not cause any exception

        # markdown test, after save, html should translated by markdown

        # after save, text should be the same
        pass
