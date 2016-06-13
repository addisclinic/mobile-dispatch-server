''' Core features of the Sana Mobile Dispatch Server

:Authors: Sana Dev Team
:Version: 2.0
'''
try:
    import json
except ImportError:
    import simplejson as json
import logging

from django.core.urlresolvers import get_resolver, get_callable, get_script_prefix, reverse
from django.conf import settings
from django.contrib.auth import authenticate

AUTH_SUCCESS = u"Successful authorization, {username}"
AUTH_FAILURE = u"Unsuccessful authorization, {username}"
AUTH_DISABLED = u"Disabled account, {username}"

# for the sana dispatcher
SIGNALS = 'signals'

# Signals for upstream web service dispatches
WSDISPATCHERS = 'WSdispatchers'

# Logging constants
LOG_SIGNAL = 'logger'
LOGGING_ENABLED = 'LOGGING_ENABLE'
LOGGING_START = 'LOGGING_START_TIME'
LOGGER = 'logger'

VERBOSITY = ('SUMMARY', 'DETAIL','VERBOSE')

CRITICAL = 32
FATAL = CRITICAL
ERROR = 16
WARNING = 8
WARN = WARNING
INFO = 4
DEBUG = 2
NOTSET = 0

LOG_LEVELS = { 'CRITICAL': 32,
           'FATAL' : CRITICAL,
           'ERROR' : 16,
           'WARNING' : 8,
           'WARN' : WARNING,
           'INFO' : 4,
           'DEBUG' : 2,
           'NOTSET' : 0 }
LEVEL_CHOICES = ((16, 'ERROR'),(16,'WARN'),('INFO' , 4),('DEBUG',2),('NOTSET',0))

CRUD = ("POST", "GET","PUT","DELETE")
crud = ("create", "read","update","delete")

# version strings
_MAJOR_VERSION = '2'
_MINOR_VERSION = '0'



def version(): 
    return settings.API_VERSION

API_VERSION = { u'API':settings.API_VERSION } 
API_CONFIG_ERROR = u'Incorrect dispatch configuration'


def do_authenticate(request):
    """ Performs a user authentication check and returns one of the following:
    
        True, "username and password validated!"
        False, "Disabled account."
        False, "username and password combination incorrect!"
        
        Requires the request have "username" and "password" parameters
        Parameters:
            request
                the request to authenticate
    """
    uname = ''
    pw = ''
    if request.method == "POST":
        uname = request.POST['username']
        pw = request.POST['password']
    else:
        uname = request.REQUEST.get("username",'')
        pw = request.REQUEST.get("password",'')
        
    result, msg = False, "Invalid auth. {uname}".format(uname=uname)
    # require non empty username and password    
    if uname and pw:
        user = authenticate(username=uname, password=pw)
        if user is not None:
            if user.is_active:
                result, msg = True, AUTH_SUCCESS.format(username=uname)
            else:
                result, msg = False, AUTH_DISABLED.format(username=uname)
        else:
            result, msg = False, AUTH_FAILURE.format(username=uname)
    return result, msg


    