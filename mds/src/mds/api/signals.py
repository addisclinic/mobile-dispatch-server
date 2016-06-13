'''
Created on Aug 11, 2012

:author: Sana Development Team
:version: 2.0
'''
from django.dispatch import Signal

class ExternalDispatch(Signal):
    """ Simple dispatching signal. The superclass providing_args are a 
        'dispatcher' key and 'data' dictionary.
    """
    def __init__(self):
        Signal.__init__(self, providing_args=["dispatcher","data"])
        
class ExternalDispatcher(object):
    """ A handler for sending messages to external targets.  
    """
    def __init__(self, registry=None):
        """ Creates a new instance and sets the registry if provided.
        """
        self.registry = registry  
    
    def __call__(self,sender, **kwargs):
        """ Callback signal processor for dispatching upstream messages.
            sender:
                An ExternalDispatch signal
        """
        data = sender.get("data")
        self.sender = sender.get("dispatcher")
        # if we provide a registry assume that the "dispatcher" sent with the 
        # sender is a registry key
        if self.registry:
            callback = self.registry.get(self.sender)
        # Otherwise we assume the "dispatcher" is a callback
        else:
            callback = self.sender
        return callback.dispatch(**data)

class ExternalWSDispatch(Signal):
    """ Simple dispatching signal. The superclass providing_args are:
    
        wsname: 
            the remote web service name
        pargs:
            path args for formatting the path String
        data:
            POST data dictionary.
        query:
            GET query dict
    """
    def __init__(self):
        Signal.__init__(self, providing_args=["wsname","pargs","data", "query"])

class ExternalWSDispatcher(object):
    """ A handler for sending messages to external targets.  
    """
    def __init__(self, wscallback):
        """ Creates a new instance and sets the registry if provided.
        """
        self.wscallback = wscallback  
    
    def __call__(self,sender, **kwargs):
        """ Callback signal processor for dispatching upstream messages.
            sender:
                An ExternalWSDispatch signal
            kwargs:
                The data from the ExternalWSDipatch. See ExternalWSDispatch for 
                details. 
        """
        data = sender.get("data")
        wsname = sender.get("wsname")
        pargs = sender.get("pargs")
        query = sender.get("query")
        return self.callback.wsdispatch(wsname,query=query,pargs=pargs, data=data)        
        
class EventSignal(Signal):
    """A generic message to pass to an EventSignalHandler holds content for   
       marking the event   
    """
    def __init__(self):
        Signal.__init__(self, providing_args=['event'])

class EventSignalHandler(object):
    """ Class based callback implementation for marking events. Creates and 
        saves a new instance of the model passed to the __init__ method.
    """
    def __init__(self, model):
        self.model = model

    def __call__(self, sender, **kwargs):
        print self.__class__.__name__, "__call__"
        try:
            data = kwargs.get('event',None)
            if not data:
                return False
            obj = self.model(**data)
            obj.save()
            return True
        except:
            return False

class CacheSignal(Signal):
    def __init__(self):
        Signal.__init__(self, providing_args=['uri','request', 'content'])

class FileCacheSignal(Signal):
    def __init__(self):
        Signal.__init__(self, providing_args=['uri','request', 'content'])
