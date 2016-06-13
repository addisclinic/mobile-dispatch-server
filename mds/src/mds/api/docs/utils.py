'''
Created on Aug 10, 2012

:author: Sana Development Team
:version: 2.0
'''
from urlparse import urljoin
from django.utils.encoding import iri_to_uri

from django.core.urlresolvers import get_resolver, get_callable, get_script_prefix

def build_rest_scheme(request,urlpatterns):
    handles = [x.callback for x in urlpatterns]
    _models = [x.handler.model for x in handles]
    response = {}
    rels = lambda x: [z[0] for z in x._meta.get_all_related_objects_with_model()]
    childs = lambda x: [z.model._meta.object_name for z in x]
    rchilds = lambda x: childs(rels(x))
    rfe = lambda x: [z.attname for z in x._meta.fields]
    #print request
    host = request.get_host()
    path = request.get_full_path()
    root = '{0}{1}'.format(host,path)
    print root
    print request.get_full_path()
    print request.get_host()
    print request.is_secure()
    
    print request.build_absolute_uri()
    for klazz in _models:
        parent = klazz.__name__.lower()
        children = rels(klazz)
        get = {'method':'GET', 
                   'description': '',
                   'params':[],
                   'url': klazz.get_absolute_url() +"/{uuid}"}
        getlist = {'method':'GET', 
                   'description': '',
                   'params':[],
                   'url': klazz.get_absolute_url()}
        
        post = {'method':'POST', 
                   'description': '',
                   'params':[],
                   'url':klazz.get_absolute_url() +"/{uuid}"}
        put = {'method':'PUT', 
                   'description': '',
                   'params':[],
                   'url': klazz.get_absolute_url() +"/{uuid}"}
        delete = {'method':'DELETE', 
                   'description': '',
                   'params':[],
                   'url': klazz.get_absolute_url() +"/{uuid}"}
        response[parent] = [get,getlist,post,put,delete]
    return response

def build_rest_uri(request, handler, location=None):
    """
    Builds an absolute URI from the location and the variables available in
    this request. If no location is specified, the absolute URI is built on
    ``request.get_full_path()``.
    """
    current_uri = '%s://%s%s' % (request.is_secure() and 'https' or 'http',
                                     request.get_host(), request.path)
    
    if not location:
        location = current_uri
    else:
        location = urljoin(current_uri, location)
    return iri_to_uri(location)

#TODO this needs work
def handler_uri_templates(handler):
    """
    URI template processor.
    
    See http://bitworking.org/projects/URI-Templates/
    """
    def _convert(template, params=[]):
        """URI template converter"""
        paths = template % dict([p, "{%s}" % p] for p in params)
        return u'%s%s' % (get_script_prefix(), paths)
    
    def _resources(obj):
        resource_uri= None
        model = getattr(obj, 'model', None)
        if hasattr(obj,'resource_uri'):
            resource_uri = obj.resource_uri()
        elif model:
            name = model.__name__.lower()
            resource_uri = ((name, ['uuid']), (name+'-list', []))
        return resource_uri
    
    try:
        resources = _resources(handler)
        result_dict = {}
        name = handler.model.__name__
        uris = {}
        for resource_uri in resources:
            components = [None, [], {}]
        
            for i, value in enumerate(resource_uri):
                components[i] = value
        
            lookup_view_name, args, kwargs = components
            lookup_view = get_callable(lookup_view_name, True)
            possibilities = get_resolver(None).reverse_dict.getlist(lookup_view)
            for possibility, pattern in possibilities:
                for result, params in possibility:
                    if args:
                        if len(args) != len(params):
                            continue
                        uris[lookup_view_name] = _convert(result, params)
                    else:
                        if set(kwargs.keys()) != set(params):
                            continue
                        uris[lookup_view_name] = _convert(result, params)
            if uris: 
                result_dict[name] =  uris
        return result_dict 
    except:
        return None
 
