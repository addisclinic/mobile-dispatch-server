'''
Created on Feb 29, 2012

:Authors: Sana Dev Team
:Version: 2.0
'''
import logging
import cjson

from django.conf import settings
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.db.models import ForeignKey
from piston.handler import BaseHandler
from piston.utils import rc

from .decorators import validate
from .responses import succeed, error
from .utils import logstack, printstack, exception_value
from mds.utils import auth
from mds.api.contrib import backends

__all__ = ['DispatchingHandler', ]


class UnsupportedCRUDException(Exception):
    def __init__(self, value):
        self.value = value
        
    def __unicode__(self):
        return unicode(self.value)

def get_root(request):
    host = request.get_host()
    scheme = 'https' if request.is_secure() else 'http'
    result = scheme + '://' + host
    return result

def get_start_limit(request): 
    get = dict(request.GET.items())
    limit = int(get.get('limit', 0))
    start = int(get.get('start', 1))
    return start, limit

class HandlerMixin(object):
    fks = None
    m2m = None
    
    def __init__(self,*args,**kwargs):
        super(HandlerMixin,self)
        self.fks = self.get_foreign_keys()
        self.m2m = self.get_m2m_keys()
        self.model = getattr(self,'model',None)
            
    def get_foreign_keys(self):
        foreign_keys = []
        if hasattr(self,'model'):
            _meta = getattr(self,'model')._meta
        else:
            return None
        for field in _meta.fields:
            if isinstance(_meta.get_field_by_name(field.name)[0], ForeignKey):
                foreign_keys.append(field.name)
        if not foreign_keys:
            return []
        return foreign_keys
        
    def get_m2m_keys(self):
        m2m = []
        if hasattr(self,'model'):
            _meta = getattr(self,'model')._meta
        else:
            return None
        for field in _meta.many_to_many:
            m2m.append(field.name)
        return m2m

class DispatchingHandler(BaseHandler,HandlerMixin):
    """Base HTTP handler for Sana api. Uses basic CRUD approach of the  
       django-piston api as a thin wrapper around class specific functions.
    """
    exclude = ['id',]
    allowed_methods = ['GET','POST','PUT','DELETE']

    def queryset(self, request, uuid=None, **kwargs):
        qs = self.model.objects.all()
        if uuid:
            return self.model.objects.get(uuid=uuid)
        if kwargs:
            qs.filter(**kwargs)
        return qs

    @validate('POST')
    def create(self,request, uuid=None, *args, **kwargs):
        """ POST Request handler. Requires valid form defined by model of  
            extending class.
        """
        logging.info("create(): %s" % (request.user))
        if uuid:
            return self.update(request,uuid=uuid)
        try:
            # Always cache the object
            instance = self._create(request, args, kwargs)
            logging.info('created object uuid=%s' % instance.uuid)
            
            # Send to any linked backends
            _instance = backends.create(instance,auth=auth.parse_auth(request))
            # If a remote is listed as the target we 
            # assume uuuid is set by the remote
            if not settings.TARGET == 'SELF':
                if _instance:
                    if  _instance.uuid != instance.uuid:
                        logging.info('updating object uuid=%s' % _instance.uuid)
                        instance.uuid = _instance.uuid
                    else:
                        logging.info('remote uuid is equal')
                else:
                    logging.info('NoneType instance returned')
            # Persist object here
            instance.save()
            logging.info('POST success object.uuid=%s' % instance.uuid)
            return succeed(instance)
        except Exception, e:
            logging.error('ERROR')
            return self.trace(request, e)
      
    def read(self,request, uuid=None, related=None,*args,**kwargs):
        """ GET Request handler. No validation is performed. """
        logging.info("read: %s, %s, %s" % (self.model,request.method,request.user))
        try:
            if uuid and related:
                response = self._read_by_uuid(request,uuid, related=related)
            elif uuid:
                response = self._read_by_uuid(request,uuid)
            else:
                q = request.REQUEST
                if q:
                    response = BaseHandler.read(self,request, **q)
                else:
                    logging.info("No querystring")
                    response = BaseHandler.read(self,request)
            return succeed(response)
        except Exception, e:
            return self.trace(request, e)
            
    @validate('PUT')
    def update(self, request, uuid=None):
        """ PUT Request handler. Allows single item updates only. """
        logging.info("update(): %s, %s" % (request.method,request.user))
        try:
            if not uuid:
                raise Exception("UUID required for update.")
            msg = self._update(request, uuid)
            logging.info("Success updating {klazz}:{uuid}".format(
                klazz=getattr(self,'model'), uuid=uuid))
            return succeed(msg)
        except Exception, e:
            return self.trace(request, e)
    
    def delete(self,request, uuid=None):
        """ DELETE Request handler. No validation is performed. """
        logging.info("delete(): %s, %s" % (request.method,request.user))
        try:
            if not uuid:
                raise Exception("UUID required for delete.")
            msg = self._delete(uuid)
            return succeed(msg)
        except Exception, e:
            return self.trace(request, e)

    def trace(self,request, ex=None):
        try:
            if settings.DEBUG:
                logging.error(unicode(ex))
            _,message,_ = logstack(self,ex)
            return error(message)
        except:
            return error(exception_value(ex))
    
    def _create(self,request, *args, **kwargs):
        data = request.form.cleaned_data
        raw_data = request.raw_data
        klazz = getattr(self,'model')
        uuid = raw_data.get('uuid',None)
        logging.debug("uuid=%s" % uuid)
        if raw_data.has_key('uuid'):
            logging.info("RAW data has uuid: %s" % uuid)
            data['uuid'] = raw_data.get('uuid')
            #instance = klazz(**raw_data)
        if uuid:
            logging.info("Has uuid: %s" % uuid)
            if klazz.objects.filter(uuid=uuid).count() == 1:
                return self._update(request,uuid=uuid)
            
        instance = klazz(**data)
        # don't commit until we return and check backends
        #instance.save(commit=False)
        return instance
    
    
    def _read_multiple(self, request, *args, **kwargs):
        """ Returns a zero or more length list of objects.
        """
        start, limit = get_start_limit(request)
        model = getattr(self,'model')
        obj_set = model.objects.all()
        if limit:
            paginator = Paginator(obj_set, limit, 
                                  allow_empty_first_page=True)
            try:
                objs = paginator.page(start).object_list
            except (EmptyPage, InvalidPage):
                objs = paginator.page(paginator.num_pages).object_list      
        else:
            objs = obj_set
        return objs

    def _read_by_uuid(self,request, uuid, related=None):
        """ Reads an object from the database using the UUID as a slug and 
            will return the object along with a set of related objects if 
            specified.
        """
        obj = BaseHandler.read(self,request,uuid=uuid)
        if not related:
            return obj
        return getattr(obj[0], str(related) + "_set").all()

    def _update(self,request, uuid):
        logging.info("_update() %s" % uuid)
        model = getattr(self,'model')
        data = request.form.cleaned_data
        raw_data = request.raw_data
        
        obj = model.objects.get(uuid=uuid)
        if 'uuid' in raw_data.keys():
            raw_data.pop('uuid')
        for k,v in data.items():
            if k in self.fks:
                _obj = getattr(obj,k).__class__.objects.get(uuid=v)
                v = _obj
                setattr(obj,k,v)
        model.objects.filter(uuid=uuid).update(**raw_data)
        msg = model.objects.filter(uuid=uuid)
        return msg
    
    def _delete(self,uuid):
        model = getattr(self,'model')
        model.objects.delete(uuid=uuid)
        return "Successfully deleted {0}: {1}".format(model.__class__.__name__,uuid)

