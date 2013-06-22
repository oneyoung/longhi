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
        self.account = {'nickname': 'dummy',
                        'username': 'test@example.com',
                        'password': 'dummy'}

    def _register_post(self, account):
        # need to provide below fields:
        # name -- as nickname
        # email -- email address
        # passowrd --  login password
        return self.client.post(reverse('memo.views.register'), account)

    def test_register(self):
        account = self.account
        resp = self._register_post(account)
        # if register success, we should redirect
        self.assertEqual(resp.status_code, 200)

        # the same account register should fail

        # after register, we can login
        ret = self.client.login(username=account['username'], password=account['password'])
        self.assertTrue(ret)

        # wrong password should login failed
        ret = self.client.login(username=account['username'], password='wrongpwd')
        self.assertFalse(ret)
