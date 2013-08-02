from django.conf.urls import patterns, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', 'memo.views.home'),
    url(r'user/register/$', 'memo.views.register'),
    url(r'user/login/$', 'memo.views.login'),
    url(r'user/logout/$', 'memo.views.logout'),
    url(r'user/suicide/$', 'memo.views.suicide'),
    url(r'memo/io/$', 'memo.views.memo_io'),
    url(r'memo/ajax/$', 'memo.views.memo_ajax'),
    url(r'memo/write/$', 'memo.views.memo_write'),
    url(r'memo/entry/$', 'memo.views.memo_entry'),
    url(r'memo/dashboard/$', 'memo.views.memo_dashboard'),
    url(r'setting/$', 'memo.views.memo_setting'),
    url(r'setting/unsubscribe/(?P<keys>\S+)/$', 'memo.views.unsubscribe'),
    url(r'activate/(?P<keys>\S+)/$', 'memo.views.activate'),
    url(r'mailbox/$', 'memo.views.mailbox', name='mailbox'),
)
