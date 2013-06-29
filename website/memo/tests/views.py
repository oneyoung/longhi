import json
from datetime import date, timedelta
from django.test import TestCase
from django.core.urlresolvers import reverse
from memo.utils import str2entrys, str2date, date2str
from memo.models import Entry
import utils


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

        # add this account to db
        self._register_post(self.account)

    def _register_post(self, account):
        # need to provide below fields:
        # name -- as nickname
        # email -- email address
        # passowrd --  login password
        return self.client.post(reverse('memo.views.register'), account)

    def test_register(self):
        # get register page first
        resp = self.client.get(reverse('memo.views.register'))
        self.assertEqual(resp.status_code, 200)

        account = {'username': 'testtest@test.com',
                   'password': 'testit'}
        resp = self._register_post(account)
        # if register success, we should redirect
        self.assertIn('been created', resp.content)

        # the same account register should tell you it was taken
        resp = self._register_post(account)
        self.assertIn('been taken', resp.content)

        # after register, we can login
        ret = self.client.login(username=account['username'], password=account['password'])
        self.assertTrue(ret)

        # wrong password should login failed
        ret = self.client.login(username=account['username'], password='wrongpwd')
        self.assertFalse(ret)

    def test_logout(self):
        account = self.account
        client = self.client
        client.login(username=account['username'], password=account['password'])
        auth_key = '_auth_user_id'
        self.assertIn(auth_key, client.session.keys())

        # issue a GET request to logout
        resp = client.get(reverse('memo.views.logout'))
        # after logout, should redirect to home page
        self.assertRedirects(resp, reverse('memo.views.home'))
        # check if we really logout, _auth_user_id should not in session
        self.assertNotIn(auth_key, client.session.keys())

        # POST request should the same result
        client.login(username=account['username'], password=account['password'])
        resp = client.post(reverse('memo.views.logout'))
        self.assertRedirects(resp, reverse('memo.views.home'))
        self.assertNotIn(auth_key, client.session.keys())


class EntrysTest(TestCase):
    def setUp(self):
        self.user = utils.create_user()
        self.client.login(username=utils.username, password=utils.password)

    def tearDown(self):
        self.client.logout()
        self.user.delete()

    def test_utils_str2entrys(self):
        '''
        the file format is define as following:
        (compatible with ohlife.com export format)
        --------------------------------------------------------
        YYYY-MM-DD *

        context of the entry, balabala...
        line1

        line2
        line3
        end of the context

        YYYY-MM-DD

        context of the next entry ....
        ...
        ...
        end

        --------------------------------------------------------
        1. entry started with date, plus an optional '*', indicated whether entry is stared
        2. a blank line act as a seperator between the ocntext
        3. at the end of the context, another blank line is required, too.
        4. then a new entry start
        '''

        # str2entrys take a string as input,
        # return a list, each element is a tuple(date, text, star)
        string1 = '2011-12-13 *\n\nfoobar\nbarfoo\n\n'
        expect = (date(2011, 12, 13), 'foobar\nbarfoo\n', True)
        result = str2entrys(string1)[0]
        self.assertTupleEqual(expect, result)

        # multiple entries test
        string2 = '2011-12-13 *\n\nfoobar\nbarfoo\n\n2011-12-13 *\n\nfoobar\nbarfoo\n\n'
        result = str2entrys(string2)
        self.assertTupleEqual(expect, result[0])
        self.assertTupleEqual(expect, result[1])

        # entry without star
        string3 = '2011-12-13\n\nfoobar\nbarfoo\n\n'
        expect = (date(2011, 12, 13), 'foobar\nbarfoo\n', False)
        result = str2entrys(string3)[0]
        self.assertTupleEqual(expect, result)

    def test_import_export_view(self):
        ''' this view POST request:
            1. login required
            2. parameter to determine whether import or export:
                'action' = 'import'/'export'
            3. file parameter is userd as uploaded file in 'import' action
        '''
        client = self.client
        user = self.user
        url = reverse('memo.views.memo_io')

        # ** import test **
        filename = 'entry_import.txt'
        import_file = utils.get_file(filename)
        # and then import file
        with open(import_file) as fp:
            client.post(url, {'action': 'import', 'file': fp})
        # here we check the result
        for date, text, star in str2entrys(utils.read_file(filename)):
            entry = Entry.objects.get(user=user, date=date)
            self.assertEquals(text, entry.text)
            self.assertEqual(star, entry.star)

        # ** export test **
        resp = client.post(url, {'action': 'export'})
        # check if file attached
        self.assertIn('attachment; filename=', resp.get('Content-Disposition'))
        # export file should the same as import file
        import_content = open(import_file).read()
        self.assertEquals(import_content, resp.content)

    def test_login_required(self):
        # logout first
        self.client.logout()

        def test_view(view_name):
            client = self.client
            url = reverse(view_name)
            redirect_url = reverse('memo.views.login') + '?next=%s' % url

            def valid_resp(resp):
                self.assertRedirects(resp, redirect_url)
                # if we login by this url, should go to original url
                ret = client.post(redirect_url, {'username': utils.username,
                                                 'password': utils.password, })
                self.assertRedirects(ret, url)
                # logout after test
                client.logout()

            # GET test
            resp = client.get(url)
            valid_resp(resp)
            # POST test
            resp = client.post(reverse(view_name), {})
            valid_resp(resp)

        views2test = ['memo.views.memo_io']
        for view_name in views2test:
            test_view(view_name)

    def test_ajax_request_post(self):
        url = reverse('memo.views.memo_ajax')
        client = self.client
        user = self.user

        def post_entry(date, star, text=''):
            request = {
                'date': date2str(date),
                'star': star,
            }
            if text:
                request['text'] = text

            resp = client.post(url, json.dumps(request), 'text/json',
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            resp_json = json.loads(resp.content)
            if not resp_json['status']:
                print resp_json['msg']
            return resp_json

        entry_date = date.today()
        entry_text = 'balabala\n'
        result = post_entry(entry_date, False, entry_text)
        # the response status should be true
        self.assertTrue(result['status'])
        # got the entry and compare
        entry0 = user.entry_set.get(date=entry_date)
        self.assertFalse(entry0.star)
        self.assertEquals(entry0.text, entry_text)

        # star the entry only
        result = post_entry(entry_date, True)
        # the response status should be true
        self.assertTrue(result['status'])
        # got the entry and compare
        entry0 = user.entry_set.get(date=entry_date)
        self.assertTrue(entry0.star)
        self.assertEquals(entry0.text, entry_text)

    def test_ajax_request_get(self):
        client = self.client
        user = self.user

        # first, let's create a bunch of entrys
        base_date = date(2013, 1, 1)
        for delta in range(60):
            current = base_date + timedelta(delta)
            utils.create_entry(user=user, date=current, text='balaba')

        def do_request(mode, query, value='', text=False):
            import urllib
            base_url = reverse('memo.views.memo_ajax')
            params = {'mode': mode, 'query': query}
            if value:
                params['value'] = value
            if text:
                params['text'] = 'true'
            url = base_url + '?%s' % urllib.urlencode(params)
            resp = client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            resp_json = json.loads(resp.content)
            if not resp_json['status']:  # print error msg when request failed
                print resp_json['msg']
            return resp_json

        # --> single query test <--
        def single_query(query, value=None, text=False):
            resp = do_request('single', query, date2str(value) if value else '', text)
            # should success and only one query return
            self.assertTrue(resp['status'])
            self.assertEqual(1, resp['count'])
            # get the entry
            e = resp.get('entries')[0]
            entry = {
                'date': str2date(e['date']),
                'star': e['star'],
                'html': e['html'],
            }
            if text:
                entry['text'] = e['text']
            return entry

        query_date = date(2013, 1, 15)
        # query=date
        query = single_query('date', query_date)
        self.assertEqual(query_date, query['date'])
        # query=next
        query = single_query('next', query_date)
        self.assertEqual(query_date + timedelta(1), query['date'])
        # query=prev
        query = single_query('prev', query_date)
        self.assertEqual(query_date - timedelta(1), query['date'])
        # query=random
        query1 = single_query('random')
        query2 = single_query('random')
        self.assertNotEqual(query1['date'], query2['date'])  # unlikely to get same query

        # text test
