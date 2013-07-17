import datetime
from django.utils import timezone
from models import Setting
import mailer

# we all use UTC time here
timezone.activate(timezone.utc)


def update_task(setting):
    if setting.notify:
        t = datetime.date.today()
        utctime = datetime.datetime(t.year, t.month, t.day)
        nexttime = (utctime + setting.utc_offset()).replace(tzinfo=timezone.utc)
    else:
        nexttime = None
    # only touch nexttime field
    Setting.objects.filter(user=setting.user).update(nexttime=nexttime)


def do_notify():
    ''' very simple notify routine '''
    now = datetime.datetime.utcnow()
    for s in Setting.objects.filter(notify=True):
        if now.toordinal() >= s.nexttime.toordinal():  # time to notify
            date = (now + s.timezone_offset()).date()  # get right date
            user = s.user
            # avoid duplicate notify
            if not user.entry_set.filter(date=date).exists():
                ee = mailer.alloc_email_entry(user, date)
                msg = mailer.notify_email(ee)
                msg.send()
            # prepare for next notify
            update_task(s)
