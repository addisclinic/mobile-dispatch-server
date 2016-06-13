''' mds.tasks.urls

:author: Sana Development Team
:version: 2.0
:copyright: Sana 2012, released under BSD New License(http://sana.mit.edu/license)
'''
from django.conf.urls import patterns, url, include

from .resources import etask_rsrc, otask_rsrc, status_rsrc

urlpatterns = patterns(    
    'tasks',
    # encounter tasks  
    url(r'^encounter/$', etask_rsrc, name='encounter-task-list'),
    url(r'^encounter/(?P<uuid>[^/]+)/$', etask_rsrc, name='encounter-task'),
    # observation tasks
    url(r'^observation/$', otask_rsrc, name='observation-task-list'),
    url(r'^observation/(?P<uuid>[^/]+)/$', otask_rsrc, name='observation-task'),
    url(r'^status/$', status_rsrc, name='status'),
    )
