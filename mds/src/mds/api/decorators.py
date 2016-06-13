'''
Created on Aug 9, 2012

:author: Sana Development Team
:version: 2.0
'''
import logging
import cjson

from . import LOGGING_ENABLED, LOG_SIGNAL, SIGNALS, LOGGER, CRUD, crud
from .responses import error, fail


from django.forms.models import modelform_factory
from django.utils.translation import ugettext_lazy as _
from piston.utils import validate, rc, decorator

from django.core.signals import request_finished, got_request_exception, Signal
from django.db import models
from .utils import make_uuid, dictzip

def enable_logging(f):
    """ Decorator to enable logging on a Django request method.
    """
    def new_f(*args, **kwargs):
        request = args[0]
        setattr(request, LOGGING_ENABLED, True)
        return f(*args, **kwargs)
    new_f.func_name = f.func_name
    return new_f

CRUD_MAP = dictzip(CRUD,crud)


def _signal(klazz, name, f):
    def new_f(*args, **kwargs):
        request = args[1]
        signals = getattr(klazz, SIGNALS, None)
        signal,callback = signals.get(name, (None,None)) if signals else (None,None)
        if signal and callback:
            signal.connect(callback)
        setattr(request, name, signal)
        return f(*args, **kwargs)
    new_f.func_name = f.func_name
    return new_f

def logged(klazz):
    """ Decorator to enable logging on a Piston Handler classes CRUD methods.
        Checks for the 'allowed_methods' class attribute to determine which
        methods to log.
        
        Looks for a (Signal, callable) assigned as the value of the 'logger' 
        key in the class.
    """
    # wraps each of the methods declared in the classes 
    # allowed_methods class to enable logging
    methods = getattr(klazz,'allowed_methods',CRUD)
    for m in methods:
        attr = CRUD_MAP.get(m,None)
        if not attr:
            continue
        f = getattr(klazz, attr)
        if f:
            setattr(klazz, attr, _signal(klazz, LOGGER, f))
    return klazz 

def universal(klazz):
    """ Decorator that declares a unique name field to a Model class. """
    field = models.CharField(max_length=36, unique=True,
                             default = make_uuid,
                             primary_key=True)
    setattr(klazz,'uuid',field)

def cacheable(klazz):
    """ Decorator that declares a unique name field to a Model class. """
    
    methods = getattr(klazz,'allowed_methods',[])
    for m in methods:
        attr = CRUD_MAP.get(m,None)
        f = getattr(klazz, attr)
        if f:
            setattr(klazz, attr, _signal(klazz,f))
    return klazz

def validate(operation='POST'):
    ''' Adds the following attributes to all CRUD requests
        
        Request.FORM         => the raw dispatchable content
        Request.CONTENT      => the dispatchable object
        
        Adds the following to the form
        Request.FORMAT       => the output format
        
        The Request.$VALUE are field names taken from api.fields module.
        
        This implementation requires all requests to have valid form data.
    '''
    @decorator
    def wrap(f, handler, request, *a, **kwa):
        # gets the form we will validate
        logging.info("request from %s" % request.user)
        klass = handler.__class__
        if hasattr(klass, 'form'):
            # want to start encouraging use of form
            v_form = getattr(klass, 'form')
        elif hasattr(klass, 'v_form'):
            # old validate form,v-form, notation
            v_form = getattr(klass, 'v_form')
        elif hasattr(klass, 'model'):
            # try to create one on the fly
            v_form = modelform_factory(model=getattr(klass, 'model'))
        else:
            return error(u'Invalid object')
        # Create the dispatchable form and validate
        logging.info("%s" % operation)
        if operation == 'POST' or operation == "PUT":
            content_type = request.META.get('CONTENT_TYPE', None)
            is_json = 'json' in content_type
            if is_json:
                data = cjson.decode(request.read())
            else:
                data = handler.flatten_dict(getattr(request, operation))
            form = v_form(data=data,files=request.FILES) if request.FILES else v_form(data=data)
            # set raw_data here to work around django form validation
            setattr(request,'raw_data', data)
            try:
                form.full_clean()
            except:
                errs = form.errors.keys()
                return fail(None, errors=errs)
                
            if not form.is_valid():
                logging.error("Form invalid")
                errs = form.errors.keys();
                return fail(None, errors=errs)
            else:
                logging.debug("FORM VALID")
        else:
            data = handler.flatten_dict(getattr(request, operation))
            form = v_form(data=data,empty_permitted=True)
        setattr(request, 'form', form)
        return f(handler, request, *a, **kwa)
    return wrap