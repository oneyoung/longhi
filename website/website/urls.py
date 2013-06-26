from django.conf.urls import patterns, url
import memo.views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', memo.views.home),
    url(r'user/register/$', memo.views.register),
    url(r'user/login/$', memo.views.login),
    url(r'user/logout/$', memo.views.logout),
    url(r'post/io/$', memo.views.post_io),
)
