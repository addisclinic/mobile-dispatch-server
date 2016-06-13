''' mds.tasks.handlers

:author: Sana Development Team
:version: 2.0
:copyright: Sana 2012, released under BSD New License(http://sana.mit.edu/license)
'''
from piston.handler import BaseHandler

from .forms import *
from .models import *
from mds.api import LOGGER
from mds.api.decorators import logged
from mds.api.handlers import DispatchingHandler
from mds.api.responses import succeed, error
from mds.api.signals import EventSignal, EventSignalHandler
from mds.core.models import Event

class StatusHandler(BaseHandler):
    model = Status
    fields = ( "current","pk")
    
@logged
class EncounterTaskHandler(DispatchingHandler):
    allowed_methods = ('GET', 'POST','PUT')
    model = EncounterTask
    form = EncounterTaskForm
    fields = (
        "uuid",
        ("assigned_to",("uuid",)),
        ("subject",("uuid")),
        ("encounter",("uuid")),
        "status",
        "due_on",
        "completed",
        "procedure")
    signals = { LOGGER:( EventSignal(), EventSignalHandler(Event))}
    
    def create(self,request,uuid=None):
        if(uuid):
            return self.update(request,uuid=uuid)
        else:
            return DispatchingHandler.create(self,request)
    
    def update(self,request,uuid=None,*args,**kwargs):
        logging.info("update() %s, %s" % (request.method,request.user))
        data = self.flatten_dict(request.POST)
        if 'uuid' in data.keys():
            uuid = data.pop['uuid']
        logging.info("update() %s" % uuid)
        
        obj = self.model.objects.get(uuid=uuid)
        status = data.pop('status', None)
        if status:
            if status.isdigit():
                obj.status = Status.objects.get(pk=int(status))
            else:
                obj.status = Status.objects.get(current__icontains=status)

        encounter = data.pop("encounter", None)
        logging.debug("....encounter:: %s" % encounter)
        if(encounter):
            obj.encounter = Encounter.objects.get(uuid=encounter)
        assigned_to = data.pop("assigned_to",None)
        if(assigned_to):
            obj.assigned_to = Observer.objects.get(uuid=assigned_to)
        subject = data.pop("subject", None)
        if(subject):
            obj.subject = Subject.objects.get(uuid=subject)
        observer = data.pop("observer",None)
        if(observer):
            obj.observer = Observer.objects.get(uuid=observer)
        for k,v in data.items():
            setattr(obj,k,v)
        obj.save()
        return succeed(self.model.objects.filter(uuid=uuid))

class ObservationTaskHandler(BaseHandler):
    allowed_methods = ("GET", "POST", "PUT", "DELETE" )
    model = ObservationTask

    def read(self,request, uuid=None):
        observer_uuid = request.GET.get("observer",None)
        if observer_uuid:
            objects = []
            try:
                observer = Observer.objects.get(uuid=observer_uuid)
                objects = ObservationTask.objects.filter(assigned_to=observer)
            except:
                pass
            return succeed(objects)
        else:
            return succeed(BaseHandler.read(self,request))