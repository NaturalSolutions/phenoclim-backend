"""
WSGI config for mysite project.
It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""
import sys
import os

# add the hellodjango project path into the sys.path
sys.path.append('/home/phenology-backend/phenoclim-backend/phenology')
# add the virtualenv site-packages path to the sys.path
sys.path.append('/home/phenology-backend/venv/lib/python2.7/sites-packages')


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "phenology.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
