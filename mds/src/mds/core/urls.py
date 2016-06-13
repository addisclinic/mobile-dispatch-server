"""The Django url to handler mappings.


:Authors: Sana dev team
:Version: 2.0
"""
from django.conf.urls import patterns, url, include

from .resources import *

# non-restful urls
urlpatterns = patterns(    
    '',
    url(r'^$', 'mds.core.views.home', name="home"),
    
    # Web views of logs
    url(r'^logs/$', 'mds.core.views.log_index', name='log-index'),
    url(r'^logs/list/$', 'mds.core.views.log_list', name='log-list'),
    url(r'^logs/detail/(?P<uuid>[^/]+)/$', 'mds.core.views.log_detail', name='log-detail'),
    url(r'^logs/report/$', 'mds.core.views.log_report', name='log-report'),
                                          
    # docs
    url(r'^docs/$', rsrc_doc, name='core-docs'),
    url(r'^mobile/authenticate/$', 'mds.core.views.mobile_authenticate', name='mobile-authenticate'),

)

urlpatterns += patterns('',
    url(r'^login/$', 'django.contrib.auth.views.login'),
)
extra_patterns = patterns(
    '',
    # session auth
    url(r'^session/$', rsrc_session, name='session-list'),
    
    # notification
    url(r'^notification/$', rsrc_notification, name='notification-list'),
    url(r'^notification/(?P<uuid>[^/]+)/$', rsrc_notification, name='notification'),
    
    # events   
    url(r'^event/$', rsrc_event, name='event-list'),
    url(r'^event/(?P<uuid>[^/]+)/$', rsrc_event, name='event'),
    
    # concepts
    url(r'^concept/$', rsrc_concept, name='concept-list'),
    url(r'^concept/(?P<uuid>[^/]+)/$', rsrc_concept, name='concept'),
    url(r'^concept/(?P<uuid>[^/]+)/relationship/$', rsrc_concept, name='concept-relationships', kwargs={'related':'relationship'}),
    url(r'^concept/(?P<uuid>[^/]+)/procedure/$', rsrc_concept, name='concept-procedures', kwargs={'related':'procedure'}),
    
    # concept relationships
    url(r'^relationship/$', rsrc_relationship,name='relationship-list'),
    url(r'^relationship/(?P<uuid>[^/]+)/$', rsrc_relationship,name='relationship'),
    
    # concept relationship categories
    url(r'^relationshipcategory/$', rsrc_relationshipcategory,
        name='relationshipcategory-list'),
    url(r'^relationshipcategory/(?P<uuid>[^/]+)/$', rsrc_relationshipcategory,
        name='relationshipcategory'),
    
    # devices
    url(r'^device/$', rsrc_device, name='device-list'),
    url(r'^device/(?P<uuid>[^/]+)/$', rsrc_device, name='device'),
    
    # encounters
    url(r'^encounter/$', rsrc_encounter, name='encounter-list'),
    url(r'^encounter/(?P<uuid>[^/]+)/$', rsrc_encounter, name='encounter'),
    url(r'^encounter/(?P<uuid>[^/]+)/(?P<related>[^/]+)/$', rsrc_encounter, name='encounter-observations', kwargs={'related':'observation'}),
    
    # observations
    url(r'^observation/$', rsrc_observation, name='observation-list'),
    url(r'^observation/(?P<uuid>[^/]+)/$', rsrc_observation, name='observation'),
    
    # observers
    url(r'^observer/$', rsrc_observer, name='observer-list'),
    url(r'^observer/(?P<uuid>[^/]+)/$', rsrc_observer, name='observer'),
    
    # procedures
    url(r'^procedure/$', rsrc_procedure, name='procedure-list'),
    url(r'^procedure/(?P<uuid>[^/]+)/$', rsrc_procedure, name='procedure'),
    
    # subjects
    url(r'^subject/$', rsrc_subject, name='subject-list'),
    url(r'^subject/(?P<uuid>[^/]+)/$', rsrc_subject, name='subject'),
    url(r'^subject/(?P<uuid>[^/]+)/encounter/$', rsrc_subject, name='subject-encounters', kwargs={'related':'procedure'}),

    #location
    url(r'^location/$', rsrc_location, name='location-list'),
)

# add the non-RESTful urls
urlpatterns += extra_patterns

