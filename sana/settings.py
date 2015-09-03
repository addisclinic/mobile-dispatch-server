"""Django settings for Sana project.

This file contains the application configuration variablesan is available with
all default values as: ::

    settings.py.tmpl

and should be renamed to settings.py prior to filling in local values. Once
updated, enter the following from the mds installation directory::

    $> ./manage.py syncdb

This will require root privileges.

:Authors: Sana Development Team
:Version: 1.1
"""

import os

DEBUG = True
''' Global debug level. Should be set to False in production environments. '''

TEMPLATE_DEBUG = DEBUG
''' Template debug level. Should be set to False in production environments. '''

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)
''' Tuple of admin names and email addresses. '''

MANAGERS = ADMINS

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DATABASE_ENGINE') or 'django.db.backends.sqlite3',
        'NAME': os.environ.get('DATABASE_NAME') or './dev.db',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

TIME_ZONE = 'America/Chicago'
"""Local time zone for this installation. Choices can be found here:

    http://en.wikipedia.org/wiki/List_of_tz_zones_by_name

although not all choices may be available on all operating systems.
If running in a Windows environment this must be set to the same as your
system time zone.
"""

LANGUAGE_CODE = 'en-us'
"""Language code for this installation. All choices can be found here:

    http://www.i18nguy.com/unicode/language-identifiers.html
"""

SITE_ID = 1
"""Don't touch this unless you know what you are doing."""


USE_I18N = True
"""If you set this to False, Django will make some optimizations so as not to
load the internationalization machinery."""

MEDIA_ROOT = ''
"""Absolute path to the directory that holds media. For a typical Sana
deployment use: "/opt/sana/media/"
"""

MEDIA_URL = ''
"""URL that handles the media served from MEDIA_ROOT. Make sure to use a
trailing slash if there is a path component (optional in other cases). For a
typical Sana deployment use: "/mds/media/". """

ADMIN_MEDIA_PREFIX = '/media/'
"""URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
trailing slash. Examples: "http://foo.com/media/", "/media/".
"""

SECRET_KEY = 'b#%x46e0f=jx%_#-a9b5(4bvxlfz-obm*gs4iu3i6k!034j(mx'
"""Make this unique, and don't share it with anybody. Seriously."""

TEMPLATE_LOADERS = [('django.template.loaders.cached.Loader', (
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
)),]
"""List of callables that know how to import templates from various sources."""

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'sana.mrs.util.LoggingMiddleware',
)
"""Don't touch this unless you know what you are doing."""

ROOT_URLCONF = 'sana.urls'
"""Don't touch this unless you know what you are doing."""

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, '/templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
"""Put strings here, like "/home/html/django_templates" or
"C:/www/django/templates". Always use forward slashes, even on Windows. Don't
forget to use absolute paths, not relative paths.For a typical Sana
deployment use: "/opt/sana/templates/"."""

INSTALLED_APPS = (
    'sana.mrs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
)
"""Don't touch this unless you know what you are doing."""

### OpenMRS settings. OpenMRS versions seem to have some difference in submitted
### date format.
OPENMRS_SERVER_URL = 'http://localhost/openmrs'
"""Change localhost when deployed."""
OPENMRS_DATE_FMT = '%m/%d/%Y %H:%M'
"""For OpenMRS ver. 1.6. Set to %d/%m/%Y when using OpenMRS 1.7."""
OPENMRS_REPLYTO = ''
"""Reply address for notifications from OpenMRS."""

### Clickatell Settings
CLICKATELL_URI = ''
"""Example 'http://api.clickatell.com/http/sendmsg?%s'"""
CLICKATELL_USER = ''
"""A valid  username."""
CLICKATELL_PASSWORD = ''
"""A valid  password."""
CLICKATELL_API = ''
"""Refer to Clickatell documentation for this value."""

### Kannel Settings
KANNEL_URI = ''
"""URI Example:  'http://127.0.0.1:12121/cgi-bin/sendsms?%s'"""
KANNEL_USER = ''
"""A valid  username."""
KANNEL_PASSWORD = ''

### ZniSMS Settings
ZNISMS_URL = ''
"""URI. Example: http://api.znisms.com/post/smsv3.asp?%s"""
ZNISMS_USER = ''
"""Consult ZniSMS documentation."""
ZNISMS_APIKEY = ''
"""Consult ZniSMS documentation."""
ZNISMS_SENDERID = ''
"""Consult ZniSMS documentation."""

### Email Configuration
EMAIL_HOST = ''
"""Outgoing mail server."""
EMAIL_HOST_USER = ''
"""Password for account used to send."""
EMAIL_HOST_PASSWORD = ''
"""Password for account used to send."""
EMAIL_PORT = ''
"""Check with mail host, i.e. gmail uses 587."""
EMAIL_USE_TLS = True
"""Check with mail host if encryption is supported"""

CONVERT_MEDIA = False
"""Set to True to convert media; i.e. if you are uploading audio or video."""

FLUSH_SAVEDPROCEDURE = False
"""Set to True to flush text data on successful send."""
FLUSH_BINARYRESOURCE = False
"""Set to True to flush file data on successful send."""
FLUSH_NOTIFICATION = False
# Set to True to flush notification data on successful send."""

