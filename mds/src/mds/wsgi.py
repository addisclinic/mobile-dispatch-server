"""
WSGI config for mds project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os,sys

path = '/opt/sana/sana.mds'
if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mds.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
