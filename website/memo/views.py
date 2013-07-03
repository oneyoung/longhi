# _*_ coding: utf8 _*_
import json
from django import http
from django.views.generic.base import View, TemplateView
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from models import User, Entry
from forms import RegisterForm
import utils


def _as_view(name, login=False):
    ''' class decorator to get a short name from django generic views
    parameters:
        name -- short name for view function
        login -- whether the view need user login
    # old style: app.views.ViewClass.as_view()
    # new style: app.views.NAME
    '''

    from django.contrib.auth.decorators import login_required

    def decorator(cls):
        globals()[name] = login_required(cls.as_view()) if login else cls.as_view()
        return cls
    return decorator


class BaseView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)
        # here we add request context for 'base.html' to
        # determine whether user login
        context['request'] = self.request
        return context


@_as_view('home')
class HomeView(BaseView):
    template_name = 'home.html'

    def get(self, request, *args, **kwargs):
        return self.render_to_response({'request': request})


@_as_view('register')
class RegisterView(BaseView):
    template_name = 'user/register.html'

    def get_context_data(self, **kwargs):
        context = super(RegisterView, self).get_context_data(**kwargs)
        context['form'] = RegisterForm
        return context

    def post(self, request, *args, **kwargs):
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            nickname = form.cleaned_data['nickname']
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(username=username, password=password)
                user.save()
                setting = user.setting
                setting.nickname = nickname
                setting.save()
                return self.render_to_response({'status': 'success'})
            else:
                return self.render_to_response({'status': 'fail', 'form': form})
        else:
            return self.render_to_response({'form': form})


def login(request):
    from django.contrib.auth.views import login as login_view
    return login_view(request,
                      template_name='user/login.html')


def logout(request):
    from django.contrib.auth import logout as dj_logout
    dj_logout(request)
    # redirect to the home page
    return redirect(reverse('memo.views.home'))


@_as_view('memo_io', login=True)
class ImportExportView(BaseView):
    template_name = 'memo/import_export.html'

    def post(self, request, *args, **kwargs):
        user = request.user
        action = request.POST.get('action')
        if action == 'import':
            f = request.FILES.get('file')
            for date, text, star in utils.str2entrys(f.read()):
                Entry(user=user, date=date, text=text, star=star).save()
        elif action == 'export':
            buf = ''.join(map(lambda e: utils.entry2str(e), user.entry_set.all()))
            resp = http.HttpResponse(buf, content_type='text/plain')
            resp['Content-Disposition'] = 'attachment; filename="entrys_export.txt"'
            return resp
        return self.render_to_response({})


@_as_view('memo_ajax', login=True)
class AjaxView(View):
    def get(self, request, *args, **kwargs):
        ''' get entry with ajax request and return json format
        URL parameters:
            mode=single:
                query=METHOD -- query method, can be 'date', 'random', 'next', 'prev', 'latest':
                    'date' -> require 'value' as target date
                    'random', 'latest' -> not other parameters required
                    'next', 'prev' -> require 'value' as baseline
                value=YYYY-MM-DD -- targeted query date, all date must be in 'YYYY-MM-DD' format
            mode=batch:
                query=all/year/month/range/star
                value=VALUE, format determined by query type
                    year -> YYYY
                    month -> YYYY-MM
                    range -> YYYY-MM-DD_YYYY-MM-DD
            text -- specified whether to fetch original text, default is 'false'

        response:
            {
                'status' = True/False, /* if request success, return True, else False */
                'msg' = 'OPTIONAL MESSAGE if REQUEST FAILED',
                'count' = NUM, /* number of entries return */
                'entries' = [
                    {'date': 'YYYY-MM-DD',
                     'star': True/False,
                     'html': 'CONTENT OF THE ENTRY IN HTML',
                     'text': 'CONTENT OF THE ENTRY IN TEXT', /* optional, return if text set */
                    },
                    { ... }, /* entry 2 */
                    ...
                ]
            }
        '''
        try:
            mode = request.GET.get('mode')
            query = request.GET.get('query')
            value = request.GET.get('value')
            text = request.GET.get('text', 'false') == 'true'
            queryset = request.user.entry_set

            def stuff_response(entrys):
                def entry2dict(entry):
                    d = {
                        'date': utils.date2str(entry.date),
                        'star': entry.star,
                        'html': entry.html
                    }
                    if text:
                        d['text'] = entry.text
                    return d

                return {
                    'status': True,
                    'msg': 'OK',
                    'count': len(entrys),
                    'entries': map(entry2dict, entrys),
                }

            if mode == 'single':  # single mode request
                if query == 'date':
                    date = utils.str2date(value)
                    entry = queryset.get(date=date)
                elif query == 'next':
                    date = utils.str2date(value)
                    entry = queryset.filter(date__gt=date).order_by('date')[0]
                elif query == 'prev':
                    date = utils.str2date(value)
                    entry = queryset.filter(date__lt=date).order_by('-date')[0]
                elif query == 'random':
                    import random
                    all_objs = queryset.all()
                    index = random.randrange(0, len(all_objs))
                    entry = all_objs[index]
                elif query == 'latest':
                    entry = queryset.latest('date')
                response = stuff_response([entry])

            elif mode == 'batch':
                if query == 'all':
                    entries = queryset.all()
                elif query == 'year':
                    year = int(value)
                    entries = queryset.filter(date__year=year)
                elif query == 'month':
                    year, month = map(int, value.split('-'))
                    entries = queryset.filter(date__year=year, date__month=month)
                elif query == 'range':
                    start, end = map(utils.str2date, value.split('_'))
                    entries = queryset.filter(date__range=(start, end))
                elif query == 'star':
                    entries = queryset.filter(star=True)
                response = stuff_response(entries.order_by('date'))
        except Exception, e:
            # we adopt a schema here: if any wrong happen, just return False
            response = {
                'status': False,
                'msg': str(e),
            }
        finally:
            return http.HttpResponse(json.dumps(response))

    def post(self, request, *args, **kwargs):
        '''
        request:
            {
                'date': 'YYYY-MM-DD',
                'star': True/False,
                'text': 'CONTENT',  /* optional field, no need for only star request */
            }
        response:
            {
                'status': True/False,
                'msg': 'OPTIONAL MESSAGE',
            }
        '''
        try:
            req_json = json.loads(request.read())
            date = utils.str2date(req_json['date'])
            user = request.user

            entry, created = Entry.objects.get_or_create(user=user, date=date)
            entry.star = req_json['star']
            text = req_json.get('text')
            if text:
                entry.text = text
            entry.save()

            response = {
                'status': True,
                'msg': 'OK',
            }
        except Exception, e:
            response = {
                'status': False,
                'msg': str(e),
            }
        finally:
            return http.HttpResponse(json.dumps(response))


@_as_view('memo_write', login=True)
class WriteView(BaseView):
    template_name = 'memo/write.html'


@_as_view('memo_entry', login=True)
class EntryView(BaseView):
    template_name = 'memo/entry.html'
