''' The base HTTP openers for OpenMRS

:author: Sana Development Team
:version: 2.0
'''
import urllib
import cookielib
import urllib2
import cjson
import re  
import base64
import logging

from mds.api.responses import succeed, fail
from mds.api.contrib.backends.handlers import AbstractHandler

__all__ = ['OpenMRSOpener', 'response_reader']

def response_reader(response):
    """ Default response handler. Returns
    """
    message = response.read()
    return succeed(message)


class OpenMRSOpener(AbstractHandler):
    """
    
    """
    
    paths = {}
    formatters = {}
    session = {}
    
    def __init__(self, host=None, auth=None):
        """Called when a new OpenMRS object is initialized.
            
        Parameters:
            host
                The OpenMRS host root url including port.
        """
        self.host = host
    
    def build_opener(self, url, username, password):
        """Builds, installs and returns an http opener using urllib2 and 
            including a MultiPartPostHandler from the contrib package.S
        """
        cookies = cookielib.CookieJar()
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, url, username, password)
        auth_handler = urllib2.HTTPBasicAuthHandler(password_mgr)
        opener = urllib2.build_opener(
                auth_handler,
                urllib2.HTTPCookieProcessor(cookies),
                handlers.MultipartPostHandler)
        urllib2.install_opener(opener)
        return opener
    
    def build_path(self,wsname,**kwargs):
        """ Returns path string by web service name key value
        """
        paths = getattr(self.__class__,"paths")
        pstring = paths.get(wsname)
        path = None
        if kwargs:
            path = pstring.format(**kwargs)
        else:
            path = pstring
        
        return path
        
    def build_url(self,wsname,pargs={},query={}):
        """ Builds the full url to the web service with the path keyed to the
            web service name
        """
        path = self.build_path(wsname, **pargs)
        # always append full rep here
        query = query if query else {}
        rep = query.get('v ', None)
        if not rep:
            query['v'] = 'full'
        qstring = urllib.urlencode(query)
        url = '{0}{1}?{2}'.format(self.host, path, qstring)
        return url
        
    def open(self, url, username=None, password=None, data=None):
        """ Opens a web service url resource """
        opener, session_key = self.open_session(username, password)
        req = urllib2.Request(url)
        if session_key:
            req.add_header("jsessionid", session_key)
        if data:
            postdata = urllib.urlencode(data)
            req.add_data(postdata)
        return opener.open(req)
    
    def open_session(self, wsname, username=None, password=None, scheme='basic'):
        """Establishes a session or auth with the web service and returns an
           opener for additional requests
        
           currently only supports basic auth.
        """
        # if class has no "sessions" attr bail
        skeys = getattr(self.__class__, "sessions". None)
        if not skeys:
            return None, None
        
        # if not given for the ws or the class has no default
        spath = skeys.get(wsname, None) if wsname in skeys.keys() else skeys.get("default", None)
        if not spath:
            return None
        
        # assuming we have data build up the session opener
        url = self.build_url(wsname)
        cookies = cookielib.CookieJar()
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, url, username, password)
        auth_handler = urllib2.HTTPBasicAuthHandler(password_mgr)
        opener = urllib2.build_opener(auth_handler,
                urllib2.HTTPCookieProcessor(cookies),)
        urllib2.install_opener(opener)
        req = urllib2.Request(url)
        
        #todo make this support something other than basic auth
        basic64 = lambda x,y: base64.encodestring('%s:%s' % (x, y))[:-1]
        if username and password:
            req.add_header("Authorization", "Basic %s" % basic64(username, password))
        #session = urllib2.urlopen(req)
        session = opener.open(req)
        return opener, session
        
    def create(self, path, response_handler=None,auth=None, data=None):
        """ Sends an Http POST for object creation. Returns the response object
            for post processing.
        """
        username=auth.get("username","") if auth else ""
        password=auth.get("password","") if auth else ""
        response = self.open(path, 
            username=username, 
            password=password,
            data=data)
        if response_handler:
            return response_handler(response)
        else:
            return response.read()
    
    def read(self, path, response_handler=None,auth=None,**query):
        """ Sends an Http GET request for object retrieval. If passed a query,
        it will be encoded and appended to the path
        """
        username=auth.get("username","")
        password=auth.get("password","")
        response = self.open(path, username=username, 
                         password=password)
        if response_handler:
            return response_handler(response)
        else:
            return response.read()
            
    def update(self, path, **kwargs):
        """ Sends an Http PUT for object updates. Currently calls POST method.
        """
        return self.create(path, kwargs)
    
    def delete(self, path, **kwargs):
        """ Sends an Http DELETE for object removal.
        """
        #TODO
        pass
    
    def wsdispatch(self, wsname, pargs={}, query=None, data=None, 
        auth=None, response_handler=None):
        """Dispatches a request to an upstream web service.
        
        """
        url = self.build_url(wsname, 
                             pargs=pargs,
                             query=query)
        logging.debug("Dispatch: %s, Url: %s" % (wsname, url))
        if wsname == "sessions":
            return self.open(url, auth["username"], auth["password"])
        if data:
            return self.create(url, response_handler=response_handler, auth=auth, data=data)
        else:
            query = query if query else {}
            return self.read(url, response_handler=response_handler, auth=auth, **query)
    
    