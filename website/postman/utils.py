import os


LAMSON_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'mailer')


def start_mail_server():
    cmds = [
        'lamson stop -ALL "%s" ' % os.path.join(LAMSON_DIR, 'run'),  # stop
        'lamson start -chdir "%s" ' % LAMSON_DIR,  # start
        'lamson log -chdir "%s" ' % LAMSON_DIR,  # start log server
    ]
    for cmd in cmds:
        os.system(cmd)
