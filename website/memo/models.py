# _*_ coding: utf8 _*_
from django.contrib import auth
from django.db import models


User = auth.models.User


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
    words = models.IntegerField(default=0)  # num of words
    stack = models.IntegerField(default=0)  # keeping writing times
    entrys = models.IntegerField(default=0)  # num of entrys
    record = models.IntegerField(default=0)  # highest keeping record


class Setting(models.Model):
    user = models.OneToOneField(User)


# signals here
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def user_created_hook(sender, instance, created, **kwargs):
    "auto create OneToOneField when User created"
    if created:
        Statics.objects.create(user=instance)
        Setting.objects.create(user=instance)


@receiver(pre_save, sender=Entry)
def entry_save_hook(sender, instance, **kwargs):
    "auto convert markdown to html when saving"
    import markdown
    md = markdown.Markdown(safe_mode='escape',
                           tab_length=4)
    instance.html = md.convert(instance.text)
