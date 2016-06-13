'''
Created on Aug 11, 2012

:author: Sana Development Team
:version: 2.0
'''

from mds.api.signals import EventSignal
from mds.core.models import Event

def event_signalhandler(sender, **kwargs):
    data = sender.get('event')
    obj = Event(**data)
    obj.save()

done_logging = EventSignal()

