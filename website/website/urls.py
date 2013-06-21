from django.conf.urls import patterns, url
import memo.views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', memo.views.home),
    url(r'account/register/$', memo.views.register),
)
