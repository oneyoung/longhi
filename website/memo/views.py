# _*_ coding: utf8 _*_
from django.views.generic.base import TemplateView
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

    def get_context_data(self, **kwargs):
        context = super(RegisterView, self).get_context_data(**kwargs)
        context['form'] = RegisterForm
        return context

    def post(self, request, *args, **kwargs):
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(username=username, password=password)
                user.save()
                return self.render_to_response({'status': 'success'})
            else:
                return self.render_to_response({'status': 'fail', 'form': form})
        else:
            return self.render_to_response({'form': form})
