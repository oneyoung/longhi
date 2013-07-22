# _*_ coding: utf8 _*_
from datetime import timedelta
from django.contrib.auth import models as auth_models
from django.db import models


User = auth_models.User


# a wrapper to avoid explict user data expose to db admin
def prop_wrap(prop):
    # TODO: implement decode/encode method
    def decode(value):
        return value

    def encode(value):
        return value

    def prop_get(self):
        return encode(getattr(self, prop))

    def prop_set(self, value):
        setattr(self, prop, encode(value))

    return property(prop_get, prop_set)


class Entry(models.Model):
    user = models.ForeignKey(User)
    date = models.DateField()
    star = models.BooleanField(default=False)
    _text = models.TextField()
    _html = models.TextField()

    text = prop_wrap('_text')
    html = prop_wrap('_html')


class Statics(models.Model):
    user = models.OneToOneField(User)
    entrys = models.IntegerField(default=0)  # num of entrys
    streak = models.IntegerField(default=0)  # keeping writing times
    record = models.IntegerField(default=0)  # highest keeping record
    last_update = models.DateField(null=True, blank=True)


class Setting(models.Model):
    user = models.OneToOneField(User)
    nickname = models.CharField(max_length=100)
    markdown = models.BooleanField(default=False)
    TIME_ZONE_CHOICES = (
        ('-12.0', '(GMT -12:00) Eniwetok, Kwajalein'),
        ('-11.0', '(GMT -11:00) Midway Island, Samoa'),
        ('-10.0', '(GMT -10:00) Hawaii'),
        ('-9.0', '(GMT -9:00) Alaska'),
        ('-8.0', '(GMT -8:00) Pacific Time (US & Canada)'),
        ('-7.0', '(GMT -7:00) Mountain Time (US & Canada)'),
        ('-6.0', '(GMT -6:00) Central Time (US & Canada), Mexico City'),
        ('-5.0', '(GMT -5:00) Eastern Time (US & Canada), Bogota, Lima'),
        ('-4.0', '(GMT -4:00) Atlantic Time (Canada), Caracas, La Paz'),
        ('-3.5', '(GMT -3:30) Newfoundland'),
        ('-3.0', '(GMT -3:00) Brazil, Buenos Aires, Georgetown'),
        ('-2.0', '(GMT -2:00) Mid-Atlantic'),
        ('-1.0', '(GMT -1:00) Azores, Cape Verde Islands'),
        ('0.0', '(GMT) Western Europe Time, London, Lisbon, Casablanca'),
        ('1.0', '(GMT +1:00) Brussels, Copenhagen, Madrid, Paris'),
        ('2.0', '(GMT +2:00) Kaliningrad, South Africa'),
        ('3.0', '(GMT +3:00) Baghdad, Riyadh, Moscow, St. Petersburg'),
        ('3.5', '(GMT +3:30) Tehran'),
        ('4.0', '(GMT +4:00) Abu Dhabi, Muscat, Baku, Tbilisi'),
        ('4.5', '(GMT +4:30) Kabul'),
        ('5.0', '(GMT +5:00) Ekaterinburg, Islamabad, Karachi, Tashkent'),
        ('5.5', '(GMT +5:30) Bombay, Calcutta, Madras, New Delhi'),
        ('5.75', '(GMT +5:45) Kathmandu'),
        ('6.0', '(GMT +6:00) Almaty, Dhaka, Colombo'),
        ('7.0', '(GMT +7:00) Bangkok, Hanoi, Jakarta'),
        ('8.0', '(GMT +8:00) Beijing, Perth, Singapore, Hong Kong'),
        ('9.0', '(GMT +9:00) Tokyo, Seoul, Osaka, Sapporo, Yakutsk'),
        ('9.5', '(GMT +9:30) Adelaide, Darwin'),
        ('10.0', '(GMT +10:00) Eastern Australia, Guam, Vladivostok'),
        ('11.0', '(GMT +11:00) Magadan, Solomon Islands, New Caledonia'),
        ('12.0', '(GMT +12:00) Auckland, Wellington, Fiji, Kamchatka'),
    )
    timezone = models.CharField(default='8.0', max_length=10, choices=TIME_ZONE_CHOICES)
    preferhour = models.IntegerField(default=20)
    INTERVAL_CHOICES = (
        (1, "Every day"),
        (2, "Every other day"),
        (3, "Every 3 days"),
        (5, "Every 5 days"),
        (7, "Every week"),
        (15, "Half a month"),
    )
    interval = models.IntegerField(default=1, choices=INTERVAL_CHOICES)
    notify = models.BooleanField(default=False)
    attach = models.BooleanField(default=False)  # attach an old entry when send email
    # keys for unsubscribe
    keys = models.CharField(max_length=256, blank=True, null=True)
    validated = models.BooleanField(default=False)  # email validation
    # next timestamp to send notify
    nexttime = models.DateTimeField(blank=True, null=True)

    def timezone_offset(self):
        value = float(self.timezone)
        hour = int(value)
        minute = (value - hour) * 60
        return timedelta(hours=hour, minutes=minute)

    def utc_offset(self):
        ''' next notify time offset to UTC 0:00
            return a timedelta object
        '''
        hours = (self.interval - 1) * 24
        return timedelta(hours=hours) + self.timezone_offset() + timedelta(hours=self.preferhour)


class EmailEntry(models.Model):
    keys = models.CharField(max_length=256, unique=True)
    date = models.DateField()
    user = models.ForeignKey(User)


# signals here
from django.db.models.signals import post_save, pre_save, post_init
from django.dispatch import receiver


@receiver(post_save, sender=User)
def user_created_hook(sender, instance, created, **kwargs):
    "auto create OneToOneField when User created"
    if created:
        Statics.objects.create(user=instance)
        Setting.objects.create(user=instance)
        # send activate email
        import mailer
        mailer.activate_email(instance).send()


@receiver(pre_save, sender=Entry)
def entry_save_hook(sender, instance, **kwargs):
    "auto convert to html when saving"
    entry = instance
    if entry.user and entry.user.setting.markdown:  # check user setting
        import markdown
        md = markdown.Markdown(safe_mode='escape',
                               tab_length=4)
        entry.html = md.convert(entry.text)
    else:
        import xml.sax.saxutils
        # we need to escape user input first to make sure html safe
        text = xml.sax.saxutils.escape(entry.text)
        # need to add <p> in every paragraph
        entry.html = ''.join(map(lambda l: '<p>%s</p>' % l, text.split('\n')))


@receiver(post_save, sender=Entry)
def entry_created_hook(sender, instance, created, **kwargs):
    entry = instance
    user = entry.user
    if created and user:
        statics = user.statics
        statics.entrys = Entry.objects.filter(user=user).count()
        if statics.last_update:
            from datetime import timedelta
            delta = entry.date - statics.last_update
            if delta <= timedelta(user.setting.interval):
                statics.streak += 1
            else:
                statics.streak = 0
        else:  # first entry for the user
            statics.streak = 1
        if statics.record < statics.streak:
            statics.record = statics.streak
        statics.last_update = entry.date
        statics.save()


@receiver(post_init, sender=Setting)
def setting_init_hook(sender, instance, **kwargs):
    import utils
    if not instance.keys:
        while 1:
            keys = utils.gen_keys()
            if not Setting.objects.filter(keys=keys).exists():
                instance.keys = keys
                break
