'''
Created on Aug 10, 2012

:author: Sana Development Team
:version: 2.0
'''
from django.db import models

from .utils import make_uuid

class RepresentationException(Exception):
    def __init__(self):
        super(RepresentationException, "Invalid representation")

class RESTModel(models.Model):
    """ Abstract class holding Common properties for RESTful objects. 
    
        By default this provides:
            uuid: SlugField, can not be edited and defaults to a version-4 UUID
                see sana.api.utils.make_uuid
            created: DateTimeField 
            modified: DateTiemField
            get_absolute_url: which return the absolute url to the object as
                the view with the same name as the class and the uuid. Hence,
                for an extending class Foo, the absolute url to an instance
                would return something like '/app/foo/foo.uuid' 
                
    """
    class Meta:
        abstract = True
        ordering = ['created']
    include_link = ('uuid', 'uri')
    include_default = ('uuid', 'uri')
    include_full = ('uuid', 'uri')
    
    _include_format = "include_{0}"
        
    uuid = models.SlugField(max_length=36, unique=True, default=make_uuid, editable=False)
    """ A universally unique identifier """
    
    created = models.DateTimeField(auto_now_add=True)
    """ When the object was created """
    
    modified = models.DateTimeField(auto_now=True)
    """ updated on modification """
    
    @models.permalink
    def get_absolute_url(self):
        """ Provides the absolute url to the object as the view with the same 
            name as the class and the uuid. Hence, for an extending class Foo, 
            the absolute url to an instance would return something like 
                /app/foo/foo.uuid
            assuming the app had declared
                url(r'^foo/(?P<uuid>[^/]+)/$)', callback, name='foo'),    
        """
        app = getattr(self._meta,'app_label')
        return ( app +':'+self._meta.module_name, [str(self.uuid)])
    
    def get_representation(self,rep='default',**kwargs):
        """ Returns a representation of this object. The three 'link', 'default'
            and 'full' methods should be overridden for custom behavior
        """
        method = "{0}_representation".format(rep)
        callable = getattr(self, method)
        representation = callable(**kwargs)
        return representation
       
    def _get_representation(self, rep, **kwargs):
        representation = {}
        rep = RESTModel._include_format.format(rep)
        for field in getattr(self.__class__, rep, ['uuid']):
            fieldobj = getattr(self, field)
            if isinstance(field, RESTModel):
                representation[field] = fieldobj.get_representation(rep=rep)
            elif callable(fieldobj):
                representation[field] = fieldobj(**kwargs)
            else:
                representation[field] = fieldobj
        return representation
       
    def uri(self, location=''):
        return location + self.get_absolute_url()
    
    def full_representation(self, **kwargs):
        """ Equivalent to self.get_representation(rep='full') """
        return self._get_representation('full', **kwargs)
    
    def link_representation(self, **kwargs):
        """ Equivalent to self.get_representation(rep='link') """
        return self._get_representation('link', **kwargs)
    
    def default_representation(self, **kwargs):
        """ equivalent to self.get_representation() """
        return self._get_representation('default', **kwargs)

        
    
    
    
        