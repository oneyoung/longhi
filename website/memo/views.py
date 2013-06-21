# _*_ coding: utf8 _*_
from django.views.generic.base import TemplateView


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
