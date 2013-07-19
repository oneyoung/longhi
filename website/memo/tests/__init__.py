from views import *
from models import *
from mailer import *
from tasks import *

'''
*** take care ***
as we put tests.py as an packages,
there is something need to take care.

*. as Django test design, this tests module is just a file,
  so it will access to all the test case as 'tests.*'

*. as note above, we need to make sure test case can be access
  under 'tests.*' namespace. so we use 'from MODULE import *'

*. take care of our import style here.
  we use 'from MODULE import *', so all the name in
  sub-module would be export to the same namespace.
  * BE CAREFUL, don't use the same name *

'''
