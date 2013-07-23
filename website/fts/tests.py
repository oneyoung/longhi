"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import os
from django.test import LiveServerTestCase
from django.core.urlresolvers import reverse
from selenium import webdriver


PROXY = os.environ.get('http_proxy', '')
if PROXY:
    PROXY_SETTINGS = webdriver.common.proxy.Proxy({
        "httpProxy": PROXY,
        "ftpProxy": PROXY,
        "sslProxy": PROXY,
        "noProxy": None,
        "class": "org.openqa.selenium.Proxy",
        "autodetect": False
    })
else:
    PROXY_SETTINGS = webdriver.common.proxy.Proxy({})


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
                                        webdriver.DesiredCapabilities.FIREFOX,
                                        proxy=PROXY_SETTINGS)
        self.browser.implicitly_wait(3)
        # create a user
        self.username = 'accout_test@test.com'
        self.password = 'xxxxxxxx'
        self.nickname = 'robot'
        # new user register
        #self.fill_register_form(self.username, self.password)
        from memo.tests.utils import create_user
        create_user(self.username, self.password, self.nickname)

    def tearDown(self):
        self.browser.quit()

    def login(self):
        self.fill_login_form(self.username, self.password)

    def reverse(self, view):
        return self.fullurl(reverse(view))

    def fullurl(self, path):
        return '%s%s' % (self.live_server_url, path)

    def fill_form(self, form):
        ''' fill the form:
            form struct:
                ((NAME, VALUE), ...)
            NAME -- name of the input element
            VALUE -- if value is string, we will user send_keys,
                    else VALUE is a bool value, and True indicate click element
        '''
        for name, value in form:
            element = self.browser.find_element_by_name(name)
            if isinstance(value, str):
                element.clear()  # should clear existing text
                element.send_keys(value)
            elif value:  # bool value deter whether to click
                element.click()

    def fill_register_form(self, username, password, password_confirm=None, submit=True):
        # open login page
        self.browser.get(self.reverse('memo.views.register'))
        # fill in the email filed
        form = (
            ('username', username),
            ('nickname', self.nickname),
            ('password', password),
            ('password_confirm', password_confirm if password_confirm else password),
            ('submit', True if submit else False),
        )
        self.fill_form(form)

    def fill_login_form(self, username, password, next='', openpage=True, submit=True):
        if openpage:
            url_base = reverse('memo.views.login')
            url_para = '?next=%s' % next if next else ''
            self.browser.get(self.fullurl(url_base + url_para))
        # fill the username and password field
        form = (
            ('username', username),
            ('password', password),
            ('submit', True if submit else False),
        )
        self.fill_form(form)

    def get_input_value(self, name):
        element = self.browser.find_element_by_name(name)
        input_type = element.get_attribute('type')
        if input_type == 'checkbox':
            return True if element.get_attribute('checked') else False
        else:
            return element.get_attribute('value')

    def assert_element_disabled(self, name, state):
        submit = self.browser.find_element_by_name(name)
        disabled = True if submit.get_attribute('disabled') else False
        assert disabled == state, "%s: desire %s, result %s" % (name, state, disabled)

    def assert_submit_button_disabled(self, state):
        self.assert_element_disabled('submit', state)

    def assert_body_contain(self, string, include=True):
        body = self.browser.find_element_by_tag_name('body')
        if include:
            self.assertIn(string, body.text)
        else:
            assert not string in body.text


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
                 'memo.views.memo_entry',
                 'memo.views.memo_setting', ]
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
        #  successful login should redirect to entry page
        self.assertEquals(self.browser.current_url,
                          self.reverse('memo.views.memo_entry'))

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
    def entry_write(self, date, star, text):
        # open the page
        url = self.reverse('memo.views.memo_write')
        self.browser.get(url)
        # we could see form that can fill date, text and whether to star
        element = self.browser.find_element_by_name('date')
        element.send_keys(date)
        element = self.browser.find_element_by_name('text')
        element.send_keys(text)
        element = self.browser.find_element_by_css_selector('.entry-form .star-btn')
        if star:
            element.click()  # star the entry
        # then submit
        element = self.browser.find_element_by_name('submit')
        element.click()

    def test_entry_write(self):
        self.login()
        url = self.reverse('memo.views.memo_write')
        self.entry_write('2013-01-01', True, 'This is a test entry.\n haha!\n')
        # we should jump to other page
        self.assertNotEquals(self.browser.current_url, url)

    def test_memo_entry(self):
        self.login()
        # first init with some entries
        entrys = [['2013-06-01', True, 'This a test entry for 0601'],
                  ['2013-06-05', True, 'This a test entry for 0605'],
                  ['2013-06-11', True, 'This a test entry for 0611']]
        for date, star, text in entrys:
            self.entry_write(date, star, text)

        def click_button_by_id(btn_id):
            btn = self.browser.find_element_by_id(btn_id)
            btn.click()

        url = self.reverse('memo.views.memo_entry')
        prev_btn = 'entry-prev-btn'
        next_btn = 'entry-next-btn'
        latest_btn = 'entry-latest-btn'
        random_btn = 'entry-latest-btn'
        self.browser.get(url)
        # after open entry page, we should see the latest entry
        self.assert_body_contain(entrys[-1][-1])

        # click previous button
        click_button_by_id(prev_btn)
        # we should see the newer entry
        self.assert_body_contain(entrys[-2][-1])
        # click again
        click_button_by_id(prev_btn)
        self.assert_body_contain(entrys[-3][-1])

        # click next button
        click_button_by_id(next_btn)
        # we should see the newer entry
        self.assert_body_contain(entrys[-2][-1])

        # click random
        click_button_by_id(random_btn)

        # click latest button
        click_button_by_id(latest_btn)
        self.assert_body_contain(entrys[-1][-1])

    def test_setting_page(self):
        url = self.reverse('memo.views.memo_setting')
        self.login()
        self.browser.get(url)  # open setting page

        success_str = "Setting Save Successfully"

        self.assert_body_contain(success_str, include=False)
        # by default notify setting would disabled, thus sub setting should be
        # disabled
        assert False == self.get_input_value('notify'), "notify should be unchecked by default"
        for name in ['timezone', 'preferhour', 'interval', 'attach']:
            self.assert_element_disabled(name, True)
        # setting the form
        form = (
            ('nickname', 'NewNick'),
            #('markdown', True),
            #('notify', True),
            #('preferhour', '14'),
            #('attach', True),
            ('submit', True),
        )
        self.fill_form(form)
        # after submit, page should say "Setting Save Successfully"
        self.assert_body_contain(success_str)
        # check the result
        for name, value in form:
            if name == 'submit':  # skip submit elem
                continue
            rel_value = self.get_input_value(name)
            assert rel_value == value, "%s: expect %s, while real %s" % (name, value, rel_value)
