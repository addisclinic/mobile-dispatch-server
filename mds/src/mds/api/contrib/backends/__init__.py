'''
Provides access to pluggable backend infrastructucture.

Target backends must be configured in the settings by adding
the desired backend to the value of the TARGET variable.
'''
import logging
import importlib
import sys, traceback

from django.conf import settings
from django.db import models as _models

from .handlers import AbstractHandler, FakeHandler
from mds.api.utils import logtb
"""
__all__ = [
    'autocreate',
    'AbstractHandler',
    'register_handler',
    'remove_handler',
    'get_handlers',
    'create',
    'read',
    'update',
    'delete',
]
"""
_handlers = {
    'Concept': [],
    'RelationShip': [],
    'RelationshipCategory':[],
    'Device': [],
    'Encounter': [],
    'Event': [],
    'Instruction': [],
    'Location':[],
    'Notification': [],
    'Procedure':[],
    'Observation':[],
    'Observer': [],
    'Procedure': [],
    'Subject':[],
    'Session': [],
}

_handler_registry = {}

def autocreate(handler_dict=None):
    ''' Auto configures the backend handlers based on the value of
        TARGETS in the settings.
    '''
    if not handler_dict:
        try:
            handler_dict = settings.TARGETS
        except:
            raise ImportError('TARGETS must be defined in settings.py')

    for model, handler_strs in handler_dict.items():
        for handlers in handler_strs:
            for handler in handler_strs:
                register_handler(model,handler)

def register_handler(model, target):
    if isinstance(target, AbstractHandler):
        handler = target
    else:
        handler_module = importlib.import_module(target)
        if hasattr(handler_module, 'get_handler'):
            handler = handler_module.get_handler(model)
        else:
            handler = FakeHandler()
    handler_list = _handlers.get(model,[])
    if not handler in handler_list:
        handler_list.append(handler)
    _handlers[model] = handler_list

def remove_handler(model, target):
    handler_list = _handlers.get(model,[])
    if not handler in handler_list:
        handler_list.append(handler)
    _handlers[model] = handler_list


def get_handler_method(handler_instance, method, model):
    method_str = '{method}_{model}'
    model = model.lower()
    method = method_str.format(method=method, model=model)
    handler_callable = getattr(handler_instance, method, None)
    return handler_callable
        

def get_handler_instance(handler_klass, **initkwargs):
        #handler_klazz = _handlers.get(handler_module)
        return handler_klass(initkwargs)

def get_handlers(model, method, **initkwargs):
    ''' Returns the callable for sending the instance 
        to the target.
    '''
    logging.info("get_handlers %s_%s" %(method,model))
    if isinstance(model, str):
        model = model
    if isinstance(model, _models.Model):
        model = model.__name__
    handlers = _handlers.get(model, [])
    handler_callers = [ get_handler_method(x, method, model) for x in handlers]
    return handler_callers

def dispatch(handlers, instance, auth=None,methodkwargs={}):
    ''' Invokes the callable handler for each handlers provided in the
        'handlers" iterable. The first item in the handler
    '''
    result = None
    for handler in handlers:
        try:
            _result = handler(instance, auth=auth)
            result = _result if not result else result
        except:
            logging.exception("Dispatch to backend failed")
            logtb()
    return result

def create(instance, auth=None, methodkwargs={}):
    ''' Handles the instance creation in the backend and returns a list
        of objects created.
        
        This effectively wraps a POST call to the dispatch server and
        forwards it to the frontend. The first handler registered will
        be used as the primary 
    '''
    if isinstance(instance, _models.Model):
        model = instance.__class__.__name__
    else:
        model = instance
    handlers = get_handlers(model,'create')
    result = dispatch(handlers, instance, auth=auth, methodkwargs=methodkwargs)
    return result

def read(instance, auth=None, methodkwargs={}):
    ''' Handles the instance fetch in the backend and returns a list
        of objects created.
        
        This effectively wraps a POST call to the dispatch server and
        forwards it to the frontend. The first handler registered will
        be used as the primary 
    '''
    if isinstance(instance, _models.Model):
        model = instance.__class__.__name__
    else:
        model = instance
    handlers = get_handlers(model)
    result = dispatch(handlers, instance, auth=auth,methodkwargs=methodkwargs)
    return result

def update(model, obj, auth=None, methodkwargs={}):
    ''' Handles the instance fetch in the backend and returns a list
        of objects created.
        
        This effectively wraps a PUT call to the dispatch server and
        forwards it to the frontend. The first handler registered will
        be used as the primary 
    '''
    if isinstance(instance, _models.Model):
        model = instance.__class__.__name__
    else:
        model = instance
    handlers = get_handlers(model,'update')
    result = dispatch(handlers, instance, auth=auth, methodkwargs=methodkwargs)
    return result

def delete(instance, auth=None, methodkwargs={}):
    ''' Handles the instance delete in the backend and returns a list
        of objects created.
        
        This effectively wraps a DELETE call to the dispatch server and
        forwards it to the frontend. The first handler registered will
        be used as the primary 
    '''
    if isinstance(instance, _models.Model):
        model = instance.__class__.__name__
    else:
        model = instance
    handlers = get_handlers(model,'delete')
    result = dispatch(handlers, instance, auth=auth, methodkwargs=methodkwargs)
    return result
