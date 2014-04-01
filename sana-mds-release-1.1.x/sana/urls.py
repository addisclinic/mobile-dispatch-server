"""The Django url to handler mappings for mDS.


:Authors: Sana dev team
:Version: 1.1
"""

from django.conf.urls.defaults import patterns, url

# Uncomment the next two lines to enable the admin:
#from django.contrib import admin
#admin.autodiscover()

from sana.mrs.models import RequestLog

log_list = {
    'queryset': RequestLog.objects.all().order_by('-timestamp'),
    'paginate_by': 100,
    }
log_item = {
    'queryset': RequestLog.objects.all(),
    }
log_detail = {
    'queryset': RequestLog.objects.all(),
    }

urlpatterns = patterns(
    '',
    # Example:
    # (r'^sana/', include('sana.foo.urls')),

    url(r'^$',
        'sana.mrs.views.home',
        name="sana-home"),

    url(r'^notifications/$',
        'sana.mrs.views.list_notifications',
        name="sana-list-notifications"),

    url(r'^notifications/submit/$',
        'sana.mrs.json.notification_submit',
        name="sana-api-notification-submit"),

    url(r'^notifications/submit/email/$',
        'sana.mrs.json.email_notification_submit',
        name="sana-api-email-notification-submit"),

#     url(r'^json/notifications/$',
#         'sana.mrs.json.notification_list',
#         name="sana-json-notification-list"),

     url(r'^json/patient/list/$',
         'sana.mrs.json.patient_list',
         name="sana-json-patient-list"),

     url(r'^json/patient/(?P<id>[0-9-]+)/$',
         'sana.mrs.json.patient_get',
         name="sana-json-patient-get"),

     #url(r'^json/procedure/list/$',
     #    'sana.mrs.json.procedure_list',
     #    name="sana-json-procedure-list"),

    #url(r'^json/procedure/(?P<id>\d+)/$',
    #    'sana.mrs.json.procedure_get',
    #    name="sana-json-procedure-get"),

    url(r'^json/validate/credentials/$',
        'sana.mrs.json.validate_credentials',
        name = "sana-json-validate-credentials"),

    url(r'^procedure/submit/$',
        'sana.mrs.views.procedure_submit',
        name="sana-html-procedure-submit"),

    url(r'^json/procedure/submit/$',
        'sana.mrs.json.procedure_submit',
        name="sana-json-procedure-submit"),

    url(r'^json/binary/submit/$',
        'sana.mrs.json.binary_submit',
        name="sana-json-binary-submit"),

    url(r'^json/binarychunk/submit/$',
        'sana.mrs.json.binarychunk_submit',
        name="sana-json-binarychunk-submit"),

    url(r'^json/textchunk/submit/$',
        'sana.mrs.json.binarychunk_hack_submit',
        name="sana-json-binarychunk-hack-submit"),

    url(r'^json/eventlog/submit/$',
        'sana.mrs.json.eventlog_submit',
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

    url(r'^log-detail/$',
        'sana.mrs.util.log_json_detail',
        name="log-json-detail-noarg"),

    url(r'^log-detail/(?P<log_id>\d+)$',
        'sana.mrs.util.log_json_detail',
        name="log-json-detail"),

    url(r'^log/$',
        'django.views.generic.list_detail.object_list',
        log_list,
        name="log-view"),

    url(r'^log/(?P<object_id>\d+)$',
        'django.views.generic.list_detail.object_detail',
        log_item,
        name="log-item-view"),

    # ADMIN
    #(r'^admin/(.*)', admin.site.root),
)
"""The mappings Django uses to send requests to the approriate handlers."""

from django.conf import settings
if settings.DEBUG:
    urlpatterns += patterns(
        '',
        (r'^media/(?P<path>.*)$',
         'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}),
    )
