'''
Created on Aug 11, 2012

:author: Sana Development Team
:version: 2.0
'''
from django.http import HttpResponse
import sys,traceback
import collections

def render_json_response(data):
    return JSONResponse(data)

_CODES = {
    'OK':200,
    'ACCEPTED':202,
    'BAD_REQUEST':400,
    'UNAUTHORIZED':401,
    'NOT_FOUND':404,
    'INTERNAL_ERROR':500,
    'UNAVAILABLE':503,
    }

class _code:
    def __init__(self, code):
        if code in _CODES.keys():
            self.name = code
        else:
            self.name = 'INTERNAL ERROR'
        self.code = _CODES.get(self.name)
    
    def __repr__(self):
        return u'{0}'.format(self.code)
    
    def __unicode__(self):
        return u'{0}'.format(self.code)
    
class Codes:
    ''' Standard Response codes for responses.'''
    OK = _code('OK')
    ACCEPTED = _code('ACCEPTED')
    BAD_REQUEST = _code('BAD_REQUEST')
    UNAUTHORIZED = _code('UNAUTHORIZED')
    NOT_FOUND = _code('NOT_FOUND')
    INTERNAL_ERROR = _code('INTERNAL_ERROR')
    UNAVAILABLE = _code('UNAVAILABLE')

class JSONResponse(HttpResponse):
    """ Extension of HttpResponse with X-JSON header and the mimetype set to 
        application/json and charset to settings.DEFAULT_CHARSET
        
        Parameters:
            data
                message content
    """
    def __init__(self, data):
        HttpResponse.__init__(self, data, mimetype="application/json; charset=utf-8")
        self['X-JSON'] = data

def fail(data, code=404, errors=[]):
    ''' Fail response as a python dict with data '''
    response = {'status': 'FAILURE',
                'code' : code,
                'message': data,
                'errors': errors, }
    return response

def succeed(data, code=200):
    ''' Success response as a python dict with data '''
    '''
    msg = []
    try:
        if msg.hasattr('__contains__'):
            msg = data
        else:
            msg.append(data)
    except:
        msg.append(data)
    '''
    #msg = data if isinstance(data,collections.Iterable) else data
    response = {'status': 'SUCCESS',
                'code' : code,
                'message': data, }
    return response

def error(exception):
    errors = traceback.format_exception_only(*sys.exc_info()[:2])
    response = {'status': 'FAILURE',
                'code' : code,
                'message': None,
                'errors': errors, }
    return response

def unauthorized(message):
    return fail(message, Codes.UNAUTHORIZED)
