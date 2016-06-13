"""The Django url to handler mappings for mDS.


:Authors: Sana dev team
:Version: 2.0
"""
from django.conf.urls.defaults import patterns, url, include

#from sana.mds.models import   *
#from sana.api import urls as _api
#from sana.mds import urls as _mds

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from piston.resource import Resource


# from version 1.x
from . import handlers

auth_handler = Resource(handlers.AuthHandler)
encounter_handler = Resource(handlers.SavedProcedureHandler)
notification_handler = Resource(handlers.NotificationHandler)
subject_handler = Resource(handlers.PatientHandler)
event_handler = Resource(handlers.EventHandler)
event_handler = Resource(handlers.RequestLogHandler)
admin.autodiscover()

urlpatterns = patterns(
     '',
    # Example:
    # (r'^sana/', include('sana.foo.urls')),
    
    url(r'^$', 'sana.core.views.home', name="home"),
    url(r'^notifications/$',
        notification_handler,
        name="sana-list-notifications"),

    url(r'^notifications/submit/$',
        notification_handler,
        name="sana-api-notification-submit"),

    url(r'^notifications/submit/email/$',
        notification_handler,
        name="sana-api-email-notification-submit"),

#     url(r'^json/notifications/$',
#         'sana.mrs.json.notification_list',
#         name="sana-json-notification-list"),

     #url(r'^json/procedure/list/$',
     #    'sana.mrs.json.procedure_list',
     #    name="sana-json-procedure-list"),

    #url(r'^json/procedure/(?P<id>\d+)/$',
    #    'sana.mrs.json.procedure_get',
    #    name="sana-json-procedure-get"),

     url(r'^json/patient/(?P<id>[^/]+)/$',
        subject_handler,
         name="sana-patient"),

     url(r'^json/patient/list/$',
         subject_handler,
         name="sana-patient-list"),

    url(r'^json/validate/credentials/$',
        auth_handler,
        name = "sana-json-validate-credentials"),


    url(r'^json/eventlog/submit/$',
        event_handler,
        name="sana-json-eventlog-submit"),


    #Manila Branch  saved procedure syncing    
    #url(r'^json/saved_procedure/(?P<id>[0-9-]+)/$',
    #    'sana.mrs.json.saved_procedure_get',
    #    name="sana-json-saved-procedure-get"),        

    #url(r'^json/sync_encounters/(?P<patient_id>[0-9-]+)/$',
    #    'sana.mrs.json.syc_encounters',
    #    name="sana-json-encounters-sync"),

    #url(r'^json/sync_encounters/(?P<patient_id>[0-9-]+)/(?P<encounters>[0-9:-]+)$',
    #    'sana.mrs.json.syc_encounters',
    #    name="sana-json-encounters-sync"),
        

    # LOGGING

    #url(r'^log-detail/$',
    #    'sana.mrs.views.log_detail',
    #    name="log-json-detail-noarg"),

    #url(r'^log-detail/(?P<log_id>\d+)$',
    #    'sana.mrs.views.log_detail',
    #    name="log-json-detail"),
                        


    url(r'^log/$',
        event_handler,
        name="log-view"),
    
    url(r'^log/web/$',
        event_handler,
        name="log-web-view"), 
                       
    url(r'^log/list/$',
        event_handler,
        name="requestlog-list"),
                          
    url(r'^log/(?P<uuid>[^/]+)/$',
        event_handler,
        name="requestlog"),
       

)

"""
    url(r'^log-detail/$',
        'sana.api.v1.util.log_json_detail',
        name="log-json-detail-noarg"),

    url(r'^log-detail/(?P<log_id>\d+)$',
        'sana.api.v1.util.log_json_detail',
        name="log-json-detail"),

    url(r'^log/$',
        'django.views.generic.list_detail.object_list',
        log_list,
        name="log-view"),

    url(r'^log/(?P<object_id>\d+)$',
        'django.views.generic.list_detail.object_detail',
        log_item,
        name="log-item-view"),
"""