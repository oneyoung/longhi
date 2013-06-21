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
    def test_register_post(self):
        # need to provide below fields:
        # name -- as nickname
        # email -- email address
        # passowrd --  login password
        resp = self.client.post(reverse('memo.views.register'),
                                {'name': 'dummy',
                                 'email': 'test@example.com',
                                 'password': 'dummy'})

        # if register success, we should redirect
        self.assertEqual(resp.status_code, 200)
