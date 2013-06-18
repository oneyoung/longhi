"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from django.test import LiveServerTestCase
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
