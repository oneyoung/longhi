from memo.models import User, Entry, Statics, Setting
from django.test import TestCase
from django.core import exceptions


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
        # TODO: can access Entry set
        #user.entry_set.objects.all()

        # after user delete, these should all gone
        user.delete()
        with self.assertRaises(exceptions.ObjectDoesNotExist):
            Statics.objects.get(pk=statics_pk)
        with self.assertRaises(exceptions.ObjectDoesNotExist):
            Setting.objects.get(pk=setting_pk)


class EntryTest(TestCase):
    def test_save_and_read(self):
        # save, should not cause any exception

        # markdown test, after save, html should translated by markdown

        # after save, text should be the same
        pass
