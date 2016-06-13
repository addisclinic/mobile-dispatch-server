''' mds.tasks.urls

:author: Sana Development Team
:version: 2.0
:copyright: Sana 2012, released under BSD New License(http://sana.mit.edu/license)
'''
from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication

from mds.api.authentication import DjangoAuthentication, MultiAuthentication

from .handlers import *

basic_auth = HttpBasicAuthentication(realm="BasicAuth")
django_auth = DjangoAuthentication()
auth = MultiAuthentication([basic_auth, django_auth])

etask_rsrc = Resource(EncounterTaskHandler,authentication=auth)
otask_rsrc = Resource(ObservationTaskHandler,authentication=auth)
status_rsrc = Resource(StatusHandler,authentication=auth)
