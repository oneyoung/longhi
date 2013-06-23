# _*_ coding: utf8 _*_
from django.contrib import auth
from django.db import models


User = auth.models.User


class Entry(models.Model):
    date = models.DateField()
    star = models.BooleanField(default=False)
    text = models.TextField()
    html = models.TextField()
    user = models.ForeignKey(User)


class Statics(models.Model):
    user = models.OneToOneField(User)
    words = models.IntegerField(default=0)  # num of words
    stack = models.IntegerField(default=0)  # keeping writing times
    entrys = models.IntegerField(default=0)  # num of entrys
    record = models.IntegerField(default=0)  # highest keeping record


class Setting(models.Model):
    user = models.OneToOneField(User)


# signals here
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def user_created_hook(sender, instance, created, **kwargs):
    "auto create OneToOneField when User created"
    if created:
        Statics.objects.create(user=instance)
        Setting.objects.create(user=instance)
