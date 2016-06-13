import datetime
from django.db import models

from mds.api.utils import make_uuid
from mds.core.models import Encounter, Instruction, Subject, Observer, Procedure,Concept

def default_assigned():
    now = datetime.date.today()
    year = now.year
    month = now.month
    day = now.day 
    return datetime.datetime(year,month,day,23,59,59)

def _now_plus(days):
    now = datetime.date.today()
    year = now.year if now.year < 12 else now.year + 1
    month = now.month +1 if now.month else 1
    day = now.day 
    return datetime.datetime(year,month,day)

class Status(models.Model):
    class Meta:
        verbose_name = "Task Status"
        verbose_name_plural = "Allowed status"
    current = models.CharField(max_length=128)
    """A label for the task."""

    @property 
    def name(self):
        return self.current

    def __unicode__(self):
        return self.current

class Task(models.Model):

    uuid = models.SlugField(max_length=36, unique=True, default=make_uuid, editable=False)
    """ A universally unique identifier """

    assigned_to = models.ForeignKey(Observer, to_field='uuid')
    """Who the task is assigned to"""

    status = models.ForeignKey(Status)
    """The current status."""

    due_on = models.DateTimeField()
    """ updated on modification """

    created = models.DateTimeField(auto_now_add=True)
    """ When the object was created """

    modified = models.DateTimeField(auto_now=True)
    """ updated on modification """

    started = models.DateTimeField(blank=True, null=True)
    """ Marks when task moved to being in progress """

    completed = models.DateTimeField(blank=True, null=True)
    """ Marks when task was complete """

    concept = models.ForeignKey(Concept, to_field='uuid', default="b58f5501-0b97-4abf-b564-65cc3faadbbf")

    voided = models.BooleanField(default=False)

    def is_late(self):
        now = datetime.datetime.now()
        if now > self.due_on and self.status.pk == 1:
            return True
        else:
            return False

    def due_today(self):
        now = datetime.date.today()
        delta = now - self.due_on
        if self.status.pk == 1 and delta.days == 0:
            return True
        else:
            return False

class EncounterTask(Task):
    """An encounter task that must be completed."""
    subject = models.ForeignKey(Subject, to_field='uuid')
    """Who the task will be executed on."""

    procedure = models.ForeignKey(Procedure, to_field='uuid')
    """What will be executed."""

    encounter = models.ForeignKey(Encounter, to_field='uuid', null=True, blank=True)
    """The encounter that was collected when the task was executed"""

class ObservationTask(Task):
    """A single instruction that must be executed for an encounter such as for
       follow up data collection related to the original encounter.
    """
    encounter = models.ForeignKey(Encounter, to_field='uuid')
    """Who or what the instruction will be executed on"""

    instruction = models.ForeignKey(Instruction, to_field='uuid')
    """What will be executed."""