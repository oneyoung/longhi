"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from django.test import LiveServerTestCase
from django.core.urlresolvers import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By

EMAIL_ADDR = "xxx@example.com"


class AccountTest(LiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(3)

    def tearDown(self):
        self.browser.quit()

    def test_can_browse_homepage_and_register(self):
        # someone opens his browser, and goes to the admin page
        self.browser.get(self.live_server_url + '/')

        # he finds a banner to input email address, and a button to go
        email_input = self.browser.find_element(By.NAME, 'email')
        email_input.send_keys(EMAIL_ADDR)
        email_input.submit()

        # TODO: use the admin site to create a Poll
        self.fail('finish this test')

    def test_user_register(self):
        def fill_register_form(username, password, password_confirm=''):
            # open login page
            self.browser.get(self.live_server_url + reverse('memo.views.register'))
            # fill in the email filed
            tag = self.browser.find_element(By.NAME, 'username')
            tag.send_keys(username)
            # input the passowrd
            tag = self.browser.find_element(By.NAME, 'passowrd')
            tag.send_keys(password)
            # comfirm the passowrd
            tag = self.browser.find_element(By.NAME, 'passowrd_confirm')
            tag.send_keys(password_confirm if password_confirm else password)
            # submit
            tag.submit()

        username = 'xxxx@example.com'
        password = 'xxxxxxxx'

        # new user register
        fill_register_form(username, password)
        # should say that you are successful.
        body = self.browser.find_element(By.NAME, 'body')
        self.assertIn('Successful', body.txt)

        # repeat register should failed if the same username
        fill_register_form(username, password)
        # should say account has exists
        body = self.browser.find_element(By.NAME, 'body')
        self.assertIn('exist', body.txt)
