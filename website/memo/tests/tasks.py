import pytz
import utils
from datetime import date, datetime, timedelta
from django.utils import timezone
from memo import tasks
from mailer import MailBase

tz = pytz.timezone('Asia/Shanghai')
timezone.activate(tz)


class TaskTest(MailBase):
    def test_update_task(self):
        s = self.user.setting
        # setting timezone
        s.notify = True
        s.timezone = '8.0'
        s.preferhour = 1
        s.interval = 1

        tasks.update_task(s)
        nexttime = self.user.setting.nexttime
        t = date.today()
        desired_time = datetime(t.year, t.month, t.day) + timedelta(hours=1)
        self.assertEqual(nexttime, desired_time)

        s = self.user.setting
        s.notify = False
        tasks.update_task(s)
        self.assertFalse(self.user.setting.nexttime)

    def test_do_notify(self):
        # first create 3 user here
        user1 = utils.create_user('user1@test.com')
        user2 = utils.create_user('user2@test.com')
        user3 = utils.create_user('user3@test.com')

        # clear inbox to delete all activate emails
        self.clear_inbox()

        user1.setting.notify = True
        user2.setting.notify = True
        user3.setting.notify = True

        tasks.do_notify()
