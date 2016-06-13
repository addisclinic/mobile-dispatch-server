""" A collection of utility methods

:Authors: Sana dev team
:Version: 1.1
"""

import os, sys, traceback
import time
import logging
import cjson

from django.conf import settings

LOGGING_ENABLED = 'LOGGING_ENABLE'
LOGGING_START = 'LOGGING_START_TIME'


def trace(f):
    """Decorator to add traces to a method.
    """
    def new_f(*args, **kwargs):
        extra = {'mac':'', 'type':''}
        logging.info("TRACE %s ENTER" % f.func_name,extra=extra)
        result = f(*args, **kwargs)
        logging.info("TRACE %s EXIT" % f.func_name,extra=extra)
        return result
    new_f.func_name = f.func_name
    return new_f




def log_traceback(logging):
    """Prints the traceback for the most recently caught exception to the log 
    and returns a nicely formatted message.
    """
    et, val, tb = sys.exc_info()
    trace = traceback.format_tb(tb)
    stack = traceback.extract_tb(tb)
    for item in stack:
        logging.error(traceback.format_tb(item))
    mod = stack[0]
    return "Exception : %s %s %s" % (et, val, trace[0])
    

def flush(flushable):
    """ Removes data stored for a model instance cached in this servers data 
        stores
    
        flushable => a instance of a class which provides a flush method
    """
    flush_setting = 'FLUSH_'+flushable.__class__.__name__.upper()
    if getattr(settings, flush_setting):
        flushable.flush()

def mark(module, line,*args):
    """ in code tracing util for debugging """
    print('Mark %s.%s: %s' % (module, line, args))




