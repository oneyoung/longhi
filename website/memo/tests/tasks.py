import pytz
import utils
from datetime import date, datetime, timedelta
from django.utils import timezone
from memo import tasks
from memo.models import Setting
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
        s.save()

        tasks.update_task(s)
        nexttime = Setting.objects.get(user=self.user).nexttime
        t = date.today()
        desired_time = (datetime(t.year, t.month, t.day) + timedelta(hours=1))
        self.assertEqual(desired_time.toordinal(), nexttime.toordinal())

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

        old_datetime = datetime(2000, 1, 1).replace(tzinfo=tz)

        s1 = user1.setting
        s1.notify = True
        s1.timezone = '11.0'
        s1.preferhour = 1
        s1.nexttime = old_datetime
        s1.save()

        s2 = user2.setting
        s2.notify = True
        s2.timezone = '-9.0'
        s2.preferhour = 8
        s2.nexttime = old_datetime
        s2.save()

        s3 = user3.setting
        s3.notify = True
        s3.timezone = '8.0'
        s3.preferhour = 22
        s3.nexttime = datetime(2100, 1, 1).replace(tzinfo=tz)  # future time
        s3.save()

        tasks.do_notify()

        # check result
        today = datetime.utcnow().replace(tzinfo=timezone.utc)

        mails1 = self.recv_mail(user1)
        self.assertEqual(len(mails1), 1)
        subject = mails1[0].get('Subject')
        t1 = today.astimezone(pytz.timezone('Asia/Sakhalin'))
        self.assertIn("%s %d" % (t1.strftime('%b'), t1.day), subject)
        # check next timestamp
        nexttime = Setting.objects.get(user=user1).nexttime
        self.assertTrue(old_datetime.toordinal() < nexttime.toordinal())

        mails2 = self.recv_mail(user2)
        self.assertEqual(len(mails2), 1)
        subject = mails2[0].get('Subject')
        t2 = today.astimezone(pytz.timezone('America/Juneau'))
        self.assertIn("%s %d" % (t2.strftime('%b'), t2.day), subject)

        # user3 should not recv notify mail
        mails3 = self.recv_mail(user3)
        self.assertEqual(len(mails3), 0)
