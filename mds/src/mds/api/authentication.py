"""
"""

import cjson
from django.conf import settings
from django.contrib.auth import authenticate
from piston.authentication import HttpBasicAuthentication

class HttpBasicAuthentication2(object):
    """
    Basic HTTP authenticater. Synopsis:
    
    Authentication handlers must implement two methods:
     - `is_authenticated`: Will be called when checking for
        authentication. Receives a `request` object, please
        set your `User` object on `request.user`, otherwise
        return False (or something that evaluates to False.)
     - `challenge`: In cases where `is_authenticated` returns
        False, the result of this method will be returned.
        This will usually be a `HttpResponse` object with
        some kind of challenge headers and 401 code on it.
    """
    def __init__(self, auth_func=authenticate, realm='API'):
        self.auth_func = auth_func
        self.realm = realm

    def is_authenticated(self, request):
        auth_string = request.META.get('HTTP_AUTHORIZATION', None)

        if not auth_string:
            return False
            
        try:
            (authmeth, auth) = auth_string.split(" ", 1)

            if not authmeth.lower() == 'basic':
                return False

            auth = auth.strip().decode('base64')
            (username, password) = auth.split(':', 1)
        except (ValueError, binascii.Error):
            return False
        
        request.user = self.auth_func(username=username, password=password) \
            or AnonymousUser()
                
        return not request.user in (False, None, AnonymousUser())
        
    def challenge(self):
        resp = HttpResponse("Authorization Required")
        resp['WWW-Authenticate'] = 'Basic realm="%s"' % self.realm
        resp.status_code = 401
        return resp

    def __repr__(self):
        return u'<HTTPBasic: realm=%s>' % self.realm

class BasicOrSessionAuth(HttpBasicAuthentication):
    """ Authentication handler which accepts  session based or basic 
        authentication.
    """
    


    def challenge(self):
        msg = { "status": "FAIL",
                "code": 401,
                "message" : [], 
                "errors":["Authorization Required",]}
        resp = HttpResponse(cjson.encode(msg))
        resp['WWW-Authenticate'] = 'Basic realm="%s"' % self.realm
        resp.status_code = 401
        return resp

class DjangoAuthentication(object):
    """
    Django authentication.
    http://yml-blog.blogspot.com/2009/10/django-piston-authentication-against.html
    """
    def __init__(self, login_url=None, redirect_field_name='next'):
        if not login_url:
            login_url = settings.LOGIN_URL
        self.login_url = login_url
        self.redirect_field_name = redirect_field_name
        self.request = None

    def is_authenticated(self, request):
        """
        This method call the `is_authenticated` method of django
        User in django.contrib.auth.models.

        `is_authenticated`: Will be called when checking for
        authentication. It returns True if the user is authenticated
        False otherwise.
        """
        self.request = request
        return request.user.is_authenticated()

    def challenge(self):
        """
        `challenge`: In cases where `is_authenticated` returns
        False, the result of this method will be returned.
        This will usually be a `HttpResponse` object with
        some kind of challenge headers and 401 code on it.
        """
        path = urlquote(self.request.get_full_path())
        tup = self.login_url, self.redirect_field_name, path
        return HttpResponseRedirect('%s?%s=%s' %tup)

class MultiAuthentication(object):
    """
    Authenticated Django-Piston against multiple types of authentication
    """

    def __init__(self, auth_types):
        """ Takes a list of authenication objects to try against, the default
        authentication type to try is the first in the list. """
        self.auth_types = auth_types
        self.selected_auth = auth_types[0]

    def is_authenticated(self, request):
        """
        Try each authentication type in order and use the first that succeeds
        """
        authenticated = False
        for auth in self.auth_types:
            authenticated = auth.is_authenticated(request)
            if authenticated:
                selected_auth = auth
                break
        return authenticated

    def challenge(self):
        """
        Return the challenge for whatever the selected auth type is (or the
        default auth type which is the first in the list)"""
        return self.selected_auth.challenge()
