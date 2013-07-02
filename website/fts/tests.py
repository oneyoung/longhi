"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from django.test import LiveServerTestCase
from django.core.urlresolvers import reverse
from selenium import webdriver


def start_selenium_server():
    import os
    import time
    import subprocess
    import shlex
    from os import path
    jar_name = 'selenium-server.jar'
    if os.system('pgrep -f %s' % jar_name):
        # server not running
        jar_path = path.join(path.abspath(path.dirname(__name__)),
                             'fts', 'bin', jar_name)
        cmd = 'java -jar %s &' % jar_path
        p = subprocess.Popen(shlex.split(cmd), close_fds=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(5)
        return p.pid

start_selenium_server()


class BaseTest(LiveServerTestCase):
    def setUp(self):
        self.browser = webdriver.Remote("http://localhost:4444/wd/hub",
                                        webdriver.DesiredCapabilities.FIREFOX)
        self.browser.implicitly_wait(3)
        # create a user
        self.username = 'accout_test@test.com'
        self.password = 'xxxxxxxx'
        self.nickname = 'robot'
        # new user register
        self.fill_register_form(self.username, self.password)

    def tearDown(self):
        self.browser.quit()

    def login(self):
        self.fill_login_form(self.username, self.password)

    def reverse(self, view):
        return self.fullurl(reverse(view))

    def fullurl(self, path):
        return '%s%s' % (self.live_server_url, path)

    def fill_register_form(self, username, password, password_confirm=None, submit=True):
        # open login page
        self.browser.get(self.reverse('memo.views.register'))
        # fill in the email filed
        tag = self.browser.find_element_by_name('username')
        tag.send_keys(username)
        # fill in the nickname filed
        tag = self.browser.find_element_by_name('nickname')
        tag.send_keys(self.nickname)
        # input the passowrd
        tag = self.browser.find_element_by_name('password')
        tag.send_keys(password)
        # comfirm the passowrd
        tag = self.browser.find_element_by_name('password_confirm')
        tag.send_keys(password_confirm if password_confirm else password)
        # submit
        if submit:
            tag = self.browser.find_element_by_name('submit')
            tag.click()

    def fill_login_form(self, username, password, next='', openpage=True, submit=True):
        if openpage:
            url_base = reverse('memo.views.login')
            url_para = '?next=%s' % next if next else ''
            self.browser.get(self.fullurl(url_base + url_para))
        # fill the username and password field
        tag = self.browser.find_element_by_name('username')
        tag.send_keys(username)
        tag = self.browser.find_element_by_name('password')
        tag.send_keys(password)
        if submit:
            # submit
            tag = self.browser.find_element_by_name('submit')
            tag.click()

    def assert_submit_button_disabled(self, state):
        submit = self.browser.find_element_by_name('submit')
        disabled = True if submit.get_attribute('disabled') else False
        self.assertEqual(disabled, state)

    def assert_body_contain(self, string):
        body = self.browser.find_element_by_tag_name('body')
        self.assertIn(string, body.text)


class AccountTest(BaseTest):
    def test_can_browse_homepage(self):
        # someone opens his browser, and goes to home page
        self.browser.get(self.fullurl('/'))

        # without user login, he should see the login and register button
        self.assertEquals(self.reverse('memo.views.login'),
                          self.browser.find_element_by_partial_link_text('Login').get_attribute('href'))
        self.assertEquals(self.reverse('memo.views.register'),
                          self.browser.find_element_by_partial_link_text('Register').get_attribute('href'))

        self.login()
        # after login, he could see his nickname, in below pages
        views = ['memo.views.home',
                 'memo.views.memo_io',
                 'memo.views.memo_write',
                 'memo.views.memo_entry', ]
        for view in views:
            self.browser.get(self.reverse(view))
            self.assert_body_contain(self.nickname)

    def test_user_register(self):
        username = 'xxxx@gmail.com'
        password = 'xxxxxxxx'

        # new user register
        self.fill_register_form(username, password)
        # should say that you are successful.
        self.assert_body_contain('account has been created')

        # repeat register should failed if the same username
        self.fill_register_form(username, password)
        # should say account has exists
        self.assert_body_contain('taken')

        # after registion, we can login now
        self.fill_login_form(username, password)
        # TODO: successful login should redirect to other page

        # wrong login should say 'didn't match'
        self.fill_login_form(username, 'wrong passowrd')
        self.assert_body_contain('didn\'t match')

        # --> let's do some test for form valid <--
        # * invalid email address
        self.fill_register_form('xxxxx', password, submit=False)
        self.assert_submit_button_disabled(True)
        # * short password, less than 6 chars
        self.fill_register_form(username, 'short', submit=False)
        self.assert_submit_button_disabled(True)
        # * not confirm passowrd
        self.fill_register_form(username, password,
                                password_confirm='wrong password', submit=False)
        self.assert_submit_button_disabled(True)

    def test_login(self):
        username = self.username
        password = self.password
        # --> test login form valid <--
        # * invalid username
        self.fill_login_form('invalidusername', password, submit=False)
        self.assert_submit_button_disabled(True)
        # * invalid password length
        self.fill_login_form(username, 'short', submit=False)
        self.assert_submit_button_disabled(True)

        # --> test email and password not match
        self.fill_login_form(username, 'wrongpassowrd')
        self.assert_body_contain('try again')

    def test_login_redirect(self):
        username = self.username
        password = self.password

        # test begin
        target_url = self.reverse('memo.views.memo_io')
        self.browser.get(target_url)
        # we should redirect to login page, and fill login page
        self.fill_login_form(username, password, openpage=False)
        # then we should redirect to the same target_url
        self.assertEquals(self.browser.current_url, target_url)


class MemoTest(BaseTest):
    def test_entry_write(self):
        self.login()
        # open the page
        url = self.reverse('memo.views.memo_write')
        self.browser.get(url)
        # we could see form that can fill date, text and whether to star
        element = self.browser.find_element_by_name('date')
        element.send_keys('2013-01-01')
        element = self.browser.find_element_by_name('text')
        element.send_keys('This is a test entry.\n haha!\n')
        element = self.browser.find_element_by_name('star')
        element.click()  # star the entry
        # then submit
        element = self.browser.find_element_by_name('submit')
        element.click()
        # we should jump to other page
        self.assertNotEquals(self.browser.current_url, url)
