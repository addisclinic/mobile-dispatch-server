"""The Django url to handler mappings for mDS.


:Authors: Sana dev team
:Version: 2.0
"""

from django.conf import settings
from django.conf.urls import patterns, url, include
#from django.views.generic.simple import redirect_to

from django.contrib import admin

admin.autodiscover()

from mds.api.contrib import backends
backends.autocreate()

urlpatterns = patterns(
    '',
    url(r'^$', 'mds.views.home', name="home"),
    url(r'^login/', 'django.contrib.auth.views.login'),
    url(r'^core/', include('mds.core.urls')),#, namespace='mds.core')),
    url(r'^tasks/', include('mds.tasks.urls')),#, namespace='tasks')),
    url(r'^clients/', include('mds.clients.urls',namespace='clients')),
    url(r'^web/', include('mds.web.urls', namespace='web')),#,app_name='mds')),
    # ADMIN
    (r'^admin/', include(admin.site.urls)),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
)


"""The mappings Django uses to send requests to the appropriate handlers."""

if settings.DEBUG:
    urlpatterns += patterns(
        'django.contrib.staticfiles.views',
        url(r'^static/(?P<path>.*)$', 'serve'),
        )
    urlpatterns += patterns('',
            url(r'^media/(?P<path>.*)$', 'django.views.static.serve',  {'document_root': settings.MEDIA_ROOT }),
        )

if 'v1' in settings.APICOMPAT_INCLUDE:
    from piston.resource import Resource
    from mrs.handlers import *
    
    v1auth_resource = Resource(AuthHandler)
    v1notification_resource = Resource(NotificationHandler)
    v1smtp_resource = Resource(SMTPHandler)
    v1patient_resource = Resource(PatientHandler)
    v1savedprocedure_resource = Resource(SavedProcedureHandler)
    v1event_resource = Resource(EventHandler)
    v1requestlog_resource = Resource(EventHandler)
    v1binary_resource = Resource(BinaryHandler)
    v1binarypacket_resource = Resource(BinaryPacketHandler)
    v1base64packet_resource = Resource(Base64PacketHandler)
    v1requestlog_resource = Resource(RequestLogHandler)
    
    v1patterns = patterns(
        '',
        
        url(r'^notifications/$',
            v1notification_resource,
            name="sana-list-notifications"),
    
        url(r'^notifications/submit/$',
            v1notification_resource,
            name="sana-api-notification-submit"),
    
        url(r'^notifications/submit/email/$',
            v1smtp_resource,
            name="sana-api-email-notification-submit"),
    
         url(r'^json/patient/list/$',
            v1patient_resource,
             name="sana-json-patient-list"),
    
         url(r'^json/patient/(?P<id>[0-9-]+)/$',
            v1patient_resource,
            name="sana-json-patient-get"),
    
    
        url(r'^json/validate/credentials/$',
            v1auth_resource,
            name = "sana-json-validate-credentials"),
    
        url(r'^procedure/submit/$',
            v1savedprocedure_resource,
            name="sana-html-procedure-submit"),
    
        url(r'^json/procedure/submit/$',
            v1savedprocedure_resource,
            name="sana-json-procedure-submit"),
    
        url(r'^json/binary/submit/$',
            v1binary_resource,
            name="sana-json-binary-submit"),
    
        url(r'^json/binarychunk/submit/$',
            v1binarypacket_resource,
            name="sana-json-binarychunk-submit"),
    
        url(r'^json/textchunk/submit/$',
            v1base64packet_resource,
            name="sana-json-binarychunk-hack-submit"),
    
        url(r'^json/eventlog/submit/$',
            v1event_resource,
            name="sana-json-eventlog-submit"),
        
        # LOGGING
        url(r'^log-detail/$',
            v1requestlog_resource,
            #'sana.api.v1.util.log_json_detail',
            name="log-json-detail-noarg"),
    
        url(r'^log-detail/(?P<uuid>\d+)$',
            v1requestlog_resource,
            name="log-json-detail"),
                            
        url(r'^log/$',
            v1requestlog_resource,
            name="log-view"),
        
        url(r'^log/web/$',
            v1requestlog_resource,
            name="log-web-view"), 
                           
        url(r'^log/list/$',
            v1requestlog_resource,
            name="requestlog-list"),
                              
        url(r'^log/(?P<uuid>[^/]+)/$',
            v1requestlog_resource,
            name="requestlog"),
    )
    # Add v1 compat urls
    urlpatterns += v1patterns
        
    