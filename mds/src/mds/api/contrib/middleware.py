"""
:Authors:
:Version:
"""
import logging
import time
import cjson
from django.core.urlresolvers import resolve

from mds.api import LOGGING_ENABLED, LOGGING_START, LOG_SIGNAL, NOTSET, LOG_LEVELS, ERROR, LEVEL_CHOICES
from . import handlers 

class LoggingMiddleware(object):
    """Logs exceptions with tracebacks with the standard logging module.
    """

    def __init__(self):
        self._handler = handlers.ThreadBufferedHandler()
        logging.root.setLevel(logging.NOTSET)
        logging.root.addHandler(self._handler)

    def send_save(self, request, **kwargs):
        signal =  getattr(request, LOG_SIGNAL, None)
        if not signal:
            return
        else:
            signal.send(sender=request.__class__,**kwargs)

    def process_exception(self, request, exception):
        extra = {'mac':'', 'type':''}
        logging.error("An unhandled exception occurred: %s" % exception,
                      extra=extra)
        if not hasattr(request, LOG_SIGNAL):
            return
        log = self.buildlog(request)
        self.send_save(request, event=log)

    def process_response(self, request, response):
        if not hasattr(request, LOG_SIGNAL):
            return response
        log = self.buildlog(request)
        self.send_save(request,event=log)
        return response
        
    def process_request(self, request):
        setattr(request, LOGGING_START, time.time())
        self._handler.clear_records()
        return None

    def buildlog(self, request, verbose=True):
        time_taken = -1
        if hasattr(request, LOG_SIGNAL):
            start = getattr(request, LOGGING_START)
            time_taken = time.time() - start
        
        records = self._handler.get_records()
        first = records[0] if len(records) > 0 else None
        level =  self._level(records)
        
        records = [self._record_to_json(record, first) for record in records]
        if verbose or level >= ERROR:
            records = records[:]
        else:
            records = list(records[:1])
        resolver = resolve(request.META['PATH_INFO'])
        log = { 'client': request.META['REMOTE_ADDR'],
                'path':request.path,
                'name':resolver.url_name,
                'messages': cjson.encode(records),
                'created':start, 
                'duration':time_taken,
                'level':level}
        return log


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

    def _level(self, records, initial=NOTSET):
        level = initial
        for record in records:
            level = max(level, int(LOG_LEVELS.get(record.levelname)))
        return level
