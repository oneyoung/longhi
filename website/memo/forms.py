from django import forms


class RegisterForm(forms.Form):
    username = forms.EmailField(max_length=30, label='Email')
    password = forms.CharField(max_length=100, widget=forms.widgets.PasswordInput())
