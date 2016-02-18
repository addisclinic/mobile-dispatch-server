
"""will populate the database with test notifications and whatever else"""

from django.core.management.base import BaseCommand
from sana.urls import *
from sana.mrs.models import *
import random
import string

PATIENT = 1
CLIENT = 5555555555
PROCEDURE = 1
MESSAGE = "".join([random.choice(string.digits) for i in xrange(100)])

class Command(BaseCommand):
    def _create_notification():
        patient = Patient(name="".join([random.choice(string.letters) for i in xrange(10)]),
            remote_identifier="".join([random.choice(string.digits) for i in xrange(10)]))
        patient.save()

        client = Client(name="".join([random.choice(string.digits) for i in xrange(5)]))
        client.save()

        procedure = Procedure(title='Surgery',
            procedure_guid="".join([random.choice(string.digits) for i in xrange(10)]),
            procedure='bone surgery',
            xml='dummy.xml',
           )
        procedure.save()
        message = "".join([random.choice(string.digits) for i in xrange(100)])
        n = Notification(patient_id=patient, client=client, procedure_id=procedure,
            message=message, delivered=False)
        n.save()

    def handle(self,*args,**kwargs):
        for i in range(100):
            self._create_notification()
