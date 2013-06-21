# _*_ coding: utf8 _*_
from django.views.generic.base import TemplateView


class HomeView(TemplateView):
    template_name = 'home.html'
