from django import forms
from models import Setting


class RegisterForm(forms.Form):
    username = forms.EmailField(max_length=30, label='Email')
    nickname = forms.CharField(max_length=100)
    password = forms.CharField(max_length=100, widget=forms.widgets.PasswordInput())


class SettingForm(forms.ModelForm):
    class Meta:
        model = Setting
        exclude = ('user')
