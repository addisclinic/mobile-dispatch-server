"""Sana mDS Django admin interface

:Authors: Sana dev team
:Version: 1.1
"""

from django.contrib import admin
from .models import Patient,Procedure,BinaryResource,SavedProcedure,Notification,QueueElement,RequestLog,ClientEventLog

class ProcedureAdmin(admin.ModelAdmin):
    pass

class ClientEventLogAdmin(admin.ModelAdmin):
    list_display = ('client', 'event_time', 'event_type', 'event_value', 'encounter_reference', 'patient_reference', 'user_reference',)
    list_filter = ('event_time', 'event_type', 'encounter_reference', 'patient_reference', 'user_reference',)
    date_hierarchy = 'event_time'
    exclude = ('created', 'modified',)

admin.site.register(Procedure)
admin.site.register(Patient)
admin.site.register(BinaryResource)
admin.site.register(SavedProcedure)
admin.site.register(Notification)
admin.site.register(QueueElement)
admin.site.register(RequestLog)

#admin.site.register(ClientEventLog, ClientEventLogAdmin)
