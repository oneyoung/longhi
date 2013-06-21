from django.test import TestCase
from django.core.urlresolvers import reverse


class HomeTest(TestCase):
    def test_home_access(self):
        response = self.client.get(reverse('memo.views.home'))

        # check we use the right template
        self.assertTemplateUsed(response, 'home.html')

        # check status code
        self.assertEqual(response.status_code, 200)


class AccountTest(TestCase):
    def setUp(self):
        self.account = {'name': 'dummy',
                        'email': 'test@example.com',
                        'password': 'dummy'}

    def _register_post(self, account):
        # need to provide below fields:
        # name -- as nickname
        # email -- email address
        # passowrd --  login password
        return self.client.post(reverse('memo.views.register'),
                                {'name': account['name'],
                                 'email': account['email'],
                                 'password': account['password']})

    def _login_post(self, account):
        # two filed required: email & password
        return self.client.post(reverse('memo.views.login'),
                                {'email': account['email'],
                                 'password': account['password']})

    def test_register(self):
        resp = self._register_post(self.account)
        # if register success, we should redirect
        self.assertEqual(resp.status_code, 200)

        # the same account register should fail

        # after register, we can login
