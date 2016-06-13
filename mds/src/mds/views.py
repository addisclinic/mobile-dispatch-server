import cjson
import logging
import platform

from django import get_version as django_version
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core import serializers
from django.http import HttpResponse

from django.shortcuts import render_to_response,redirect
from django.template import RequestContext 

from mds.api import version

#@login_required(login_url='/mds/login/')
def home(request):
    """Top level url. Displays standard mds response containing following
       information about the system :
        
        Django version
        Host OS
        MDS version
        
        Note: If Http "Accept" header is included and set to 
        "application/json", the returned message will be a standard MDS
        response as follows:
        
        {
            'status':'SUCCESS',
            'code':200,
            'message': { 
                'django': django_version(),
                'platform': u' '.join(platform.uname()[0:3]),
                'version': version(),
            }
        }
    """
    data = {
        'status':'SUCCESS',
        'code':200,
        'message': { 
            'django': django_version(),
            'platform': u' '.join(platform.uname()[0:4]),
            'version': version(),
        },
    }
    accept = request.META.get('HTTP_ACCEPT',None)
    if 'application/json' in request.META.get('HTTP_ACCEPT'):
        return HttpResponse(cjson.encode(data))
    else:
        return render_to_response('index.html', RequestContext(request,data))
