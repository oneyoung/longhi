# _*_ coding: utf8 _*_
from django.views.generic.base import TemplateView
from django import http
from models import User
from forms import RegisterForm


# shortcut to get a short name from django generic views
# old style: app.views.ViewClass.as_view()
# new style: app.views.NAME
def _as_view(name):
    def decorator(cls):
        globals()[name] = cls.as_view()
        return cls
    return decorator


@_as_view('home')
class HomeView(TemplateView):
    template_name = 'home.html'


@_as_view('register')
class RegisterView(TemplateView):
    template_name = 'user/register.html'

    def post(self, request, *args, **kwargs):
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(username=username, password=password)
                user.save()
                return http.HttpResponse('OK')
            else:
                return http.HttpResponseNotAllowed('User has already exists')
