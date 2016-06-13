""" An instance of data collection resulting from executing a Procedure
on a Subject.

:Authors: Sana dev team
:Version: 2.0
"""

from django.db import models
from mds.api.utils import make_uuid

class Encounter(models.Model):
    """ A completed procedure, where data has been collected
    """
    class Meta:
        app_label = "core"
                   
    def __unicode__(self):
        return "%s" % (self.uuid)
    
    uuid = models.SlugField(max_length=36, unique=True, default=make_uuid, editable=False)
    """ A universally unique identifier """
    
    created = models.DateTimeField(auto_now_add=True)
    """ When the object was created """
    
    modified = models.DateTimeField(auto_now=True)
    """ updated on modification """
    
    procedure = models.ForeignKey('Procedure', to_field='uuid')
    """ The procedure used to collect this encounter """
    
    observer = models.ForeignKey('Observer', to_field='uuid')
    """ The entity which collected the data """
    
    device = models.ForeignKey('Device', to_field='uuid')
    """ The client which collected the encounter """
    
    subject = models.ForeignKey('Subject', to_field='uuid')
    """ The subject about whom the data was collected """

    concept = models.ForeignKey('Concept', to_field='uuid')
    """ A contextual term for the encounter."""

    voided = models.BooleanField(default=False)

    @property
    def slug(self):
        return self.uuid

    #_uploaded = models.BooleanField(default=False)
    #""" Whether the saved procedure was uploaded to a remote queueing server. """
    
    #TODO move these to a manager class
    def flush(self):
        """ Removes the responses text and files for this Encounter """
        self.save()
        for obs in self.observation_set.all():
                obs.flush();
                
    def complete(self):
        complete = True
        for obs in self.observation_set.all():
            complete = complete and obs.complete()
            if not complete:
                break
        return complete

    @models.permalink
    def get_absolute_url(self):
    	return ( 'core:encounter', { self.uuid : self.uuid } )

    def __unicode__(self):
        return u'{procedure} - {subject}'.format(
            procedure=self.procedure,
            subject=self.subject)
