import os.path
from memo.models import User, Entry


def get_file(filename):
    "get file path under memo/tests/files"
    files_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'files')
    return os.path.join(files_dir, filename)


def read_file(filename):
    "open file under memo/tests/files and return the content in utf8 encoding"
    import codecs
    return codecs.open(get_file(filename), 'r', encoding='utf8').read()


def create_user():
    "create a user and then return it"
    user = 'test@test.com'
    pswd = 'memotest'
    user = User.objects.create_user(username=user, password=pswd)
    user.save()
    return user


def create_entry(date, user, text='', star=False):
    "create an entry and then return"
    entry = Entry(date=date, user=user, text=text, star=star)
    entry.save()
    return entry
