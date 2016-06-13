"""Data models for Sana Mobile Dispatch Server

:Authors: Sana dev team
:Version: 1.1
"""
import cjson
import os

from django.db import models
from django.conf import settings

from mds.core import models as core

_app = 'mrs'

class Client(models.Model):
    """ Some arbirary way to refer to a client."""
    name = models.CharField(max_length=255, unique=True)
    last_seen = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name
    
    def touch(self):
        self.save()

class ClientEventLog(models.Model):
    """ A log entry for client events
    
    """
    class Meta:
        app_label = _app
        unique_together = (('event_type', 'event_time'),)
    
    client = models.ForeignKey('Client')
    event_type = models.CharField(max_length=512)
    event_value = models.TextField()
    event_time = models.DateTimeField()

    encounter_reference = models.TextField()
    patient_reference = models.TextField()
    user_reference = models.TextField()

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


class Patient(models.Model):
    """ Someone about whom data is collected """
    class Meta:
        app_label = _app
    name = models.CharField(max_length=512)

    # the remote record identifier for the Patient, i.e. OpenMRS ID
    remote_identifier = models.CharField(max_length=1024)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

class Procedure(models.Model):
    """ A series of steps used to collect data observations 
    """
    class Meta:
        app_label = _app
    
    title = models.CharField(max_length=255)
    procedure_guid = models.CharField(max_length=255, unique=True)
    procedure = models.TextField()
    xml = models.FileField(upload_to='procedure')
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

class BinaryResource(models.Model):
    """ A binary object, stored as a file, which was collected during an 
        encounter
    """
    class Meta:
        app_label = _app
        unique_together = (('procedure', 'element_id', 'guid'),)

    def __unicode__(self):
        return "BinaryResource %s %s %d/%d" % (self.procedure.guid,
                                               self.created,
                                               self.upload_progress,
                                               self.total_size)

    # the instance of a procedure which this binary resource is associated with
    procedure = models.ForeignKey('SavedProcedure')

    # the element id to which this binary resource applies
    element_id = models.CharField(max_length=255)

    guid = models.CharField(max_length=512)

    content_type = models.CharField(max_length=255)
    data = models.FileField(upload_to='binary/%Y/%m/%d', )

    # the current number of bytes stored for the resource
    upload_progress = models.IntegerField(default=0)
    # the binary size in bytes
    total_size = models.IntegerField(default=0)

    # Whether the binary resource was uploaded to a remote queueing
    # server.
    uploaded = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    
    # Whether type will be converted before upload
    convert_before_upload = models.BooleanField(default=False)
    
    # Whether the data has been converted. Binaries which do not need to be
    # converted before upload are considered to be in a state where conversion
    # is complete 
    conversion_complete = models.BooleanField(default=True)

    def receive_completed(self):
        """ Indicates whether the client has uploaded this entire
            binary resource to the MDS. 
        """
        return self.total_size > 0 and self.total_size == self.upload_progress

    def ready_to_convert(self):
        """ Indicates whether binary is ready to be converted. Binaries which do
            not need to be converted will return False.
        """
        return (self.receive_completed() and 
                (self.convert_before_upload == True) and
                (self.conversion_complete == False))

    def ready_to_upload(self):
        """ Indicates whether binary upload and conversion are complete
        """
        return (self.receive_completed() and 
                (self.conversion_complete == True))

    def filename(self):
        return "%s_%s" % (self.procedure.guid, self.element_id)

    def flush(self):
        """ Removes any file on disk that was created for this object.
        
            Sets the path assigned to the data field to None and commits on
            successful removal
        """
        f = self.data.path
        if f and os.path.isfile(f):
            os.remove(self.data.path)
        self.save()
        
    def create_stub(self, fname=None):
        """ Creates a zero length file stub on disk
        
            fname => a filename to assign. If None it will be auto-generated.
            Sets and updates the data field on success
        """
        #TODO add auto-generate filename
        self.data = self.data.field.generate_filename(self, fname)
        path, _ = os.path.split(self.data.path)
        # make sure we have the directory structure
        if not os.path.exists(path):
            os.makedirs(path)
        # create the stub and commit if no exceptions
        open(self.data.path, "w").close()
        self.save()
            
class SavedProcedure(models.Model):
    """ An encounter, representing a completed procedure, where data has been
        collected
    """
    class Meta:
        app_label = _app
        
    def __init__(self,*pargs,**kwargs):
        models.Model.__init__(self, *pargs, **kwargs)
        
    def __unicode__(self):
        return "SavedProcedure %s %s" % (self.guid, self.created)

    guid = models.CharField(max_length=255, unique=True)

    # GUID of the procedure this is an instance of
    procedure_guid = models.CharField(max_length=512)

    # ID of the reporting phone
    client = models.ForeignKey('Client')

    # Text responses of the saved procedure
    responses = models.TextField()

    # OpenMRS login credentials for this user
    upload_username = models.CharField(max_length=512)
    upload_password = models.CharField(max_length=512)

    # Whether the saved procedure was uploaded to a remote queueing
    # server.
    uploaded = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    # EMR Encounter Number
    # Might be cleaner to make this an integer, but EMR systems in general
    # might not use an integer as the unique ID of an encounter.
    encounter = models.CharField(default="-1", max_length=512)
    
    def flush(self):
        """ Removes the responses text and files for this SavedProcedure """
        self.responses = ''
        self.save()
        if settings.FLUSH_BINARYRESOURCE:
            for br in self.binaryresource_set.all():
                br.flush();
    
class Notification(models.Model):
    """ A message to be sent
        
        
    """
    class Meta:
        app_label = _app

    # some identifier that tells us which client it is (phone #?)
    client = models.CharField(max_length=512)
    patient_id = models.CharField(max_length=512)
    procedure_id = models.CharField(max_length=512)

    message = models.TextField()
    delivered = models.BooleanField()

    def to_json(self):
        return cjson.encode({
            'phoneId': self.client,
            'message': self.message,
            'procedureId': self.procedure_id,
            'patientId': self.patient_id
            })
        
    def flush(self):
        """ Removes the message text """
        self.message = ''
        self.save()
        
class QueueElement(models.Model):
    """ An element that is being processed
    """
    class Meta:
        app_label = _app
    procedure = models.ForeignKey('Procedure')
    saved_procedure = models.ForeignKey('SavedProcedure')

    finished = models.BooleanField()

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

TIME_FORMAT = "%m/%d/%Y %H:%M:%S"

class RequestLog(core.Event):
    """
    Logging facility for requests.
    """
    class Meta:
        app_label = _app
        
    requestlog_ptr = models.OneToOneField(core.Event, 
                                          parent_link=True,
                                          related_name="mrs_events_related")
