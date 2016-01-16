""" A collection of utility methods

:Authors: Sana dev team
:Version: 1.1
"""

import os, sys, traceback
import time
import logging
import cjson

from django.conf import settings
from django.http import HttpResponse

from sana import handler
from mrs.models import RequestLog

LOGGING_ENABLE_ATTR = 'LOGGING_ENABLE'
LOGGING_START_TIME_ATTR = 'LOGGING_START_TIME'

def enable_logging(f):
    """ Decorator to enable logging on a Django request method.
    """
    def new_f(*args, **kwargs):
        request = args[0]
        setattr(request, LOGGING_ENABLE_ATTR, True)
        return f(*args, **kwargs)
    new_f.func_name = f.func_name
    return new_f

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

def log_json_detail(request, log_id):
    log = RequestLog.objects.get(pk=log_id)

    message = {'id': log_id,
               'data': cjson.decode(log.message,True)}

    return HttpResponse(cjson.encode(message))

class LoggingMiddleware(object):
    """Logs exceptions with tracebacks with the standard logging module.
    """

    def __init__(self):
        self._handler = handler.ThreadBufferedHandler()
        logging.root.setLevel(logging.NOTSET)
        logging.root.addHandler(self._handler)

    def process_exception(self, request, exception):
        extra = {'mac':'', 'type':''}
        logging.error("An unhandled exception occurred: %s" % repr(exception),
                      extra=extra)

        time_taken = -1
        if hasattr(request, LOGGING_START_TIME_ATTR):
            start = getattr(request, LOGGING_START_TIME_ATTR)
            time_taken = time.time() - start

        records = self._handler.get_records()
        first = records[0] if len(records) > 0 else None
        records = [self._record_to_json(record, first) for record in records]
        message = cjson.encode(records)

        log_entry = RequestLog(uri=request.path,
                              message=message,
                              duration=time_taken)
        log_entry.save()

    def process_request(self, request):
        setattr(request, LOGGING_START_TIME_ATTR, time.time())
        self._handler.clear_records()
        return None

    def _time_humanize(self, seconds):
        return "%.3fs" % seconds

    def _record_delta(self, this, first):
        return self._time_humanize(this - first)

    def _record_to_json(self, record, first):
        return {'filename': record.filename,
                'timestamp': record.created,
                'level_name': record.levelname,
                'level_number': record.levelno,
                'module': record.module,
                'function_name': record.funcName,
                'line_number': record.lineno,
                'message': record.msg,
                'delta': self._record_delta(record.created, first.created)
                }

    def process_response(self, request, response):

        if not hasattr(request, LOGGING_ENABLE_ATTR):
            return response

        time_taken = -1
        if hasattr(request, LOGGING_START_TIME_ATTR):
            start = getattr(request, LOGGING_START_TIME_ATTR)
            time_taken = time.time() - start

        records = self._handler.get_records()
        first = records[0] if len(records) > 0 else None
        records = [self._record_to_json(record, first) for record in records]
        message = cjson.encode(records)

        log_entry = RequestLog(uri=request.path,
                              message = message,
                              duration=time_taken)
        log_entry.save()

        return response

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


#-------------------------------------------------------------------------------
# File utilities
#-------------------------------------------------------------------------------

kilobytes = 1024
megabytes = 1000 * kilobytes
chunksize = 100 * kilobytes
_ipath = settings.MEDIA_ROOT + 'binary/'
_opath = settings.MEDIA_ROOT + 'binary/chunk/'

def split(fin, path, chunksize=chunksize):
    """ Splits a file into a number of smaller chunks """
    print (fin, path, chunksize)
    if not os.path.exists(path):
        os.mkdir(path)
    partnum = 0
    input = open(fin, "rb")
    while True:
        chunk = input.read(chunksize)
        if not chunk:
            break
        partnum += 1
        outfile = os.path.join(path,('chunk%s' % partnum))
        fobj = open(outfile, 'wb')
        fobj.write(chunk)
        fobj.close()
    input.close()
    return partnum