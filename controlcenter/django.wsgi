import os
import sys

sys.path.append('/srv/roombaControl/controlcenter')

#os.environ['PYTHON_EGG_CACHE'] = '/srv/roombaControl/.python-egg'
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()