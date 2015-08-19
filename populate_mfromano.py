
"""will populate the database with test notifications and whatever else"""

from sana.urls import *
from sana.mrs.models import *
import random
import string

PATIENT = 1
CLIENT = 5555555555
PROCEDURE = 1
MESSAGE = "".join([random.choice(string.digits) for i in xrange(100)])

def create_notification():
    patient = "".join([random.choice(string.digits) for i in xrange(5)])
    client = "".join([random.choice(string.digits) for i in xrange(5)])
    procedure = "".join([random.choice(string.digits) for i in xrange(5)])
    message = "".join([random.choice(string.digits) for i in xrange(100)])
    n = Notification(patient_id=patient, client=client, procedure_id=procedure,
        message=message, delivered=False)
    n.save()

if __name__ == "__main__":
    for i in range(100):
        create_notification()
    for i in range(10):
        n = Notification(patient=PATIENT, client=CLIENT, procedure_id=PROCEDURE,
            message=MESSAGE, delivered=False)
        n.save()

