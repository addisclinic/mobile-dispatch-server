""" A set of instructions for data collection or information dissemination.

:Authors: Sana dev team
:Version: 2.0
"""

from django.db import models

from mds.api.utils import make_uuid

class Procedure(models.Model):
    """ A series of steps used to collect data observations. """

    class Meta:
        app_label = "core"
    uuid = models.SlugField(max_length=36, unique=True, default=make_uuid, editable=False)
    """ A universally unique identifier """
    
    created = models.DateTimeField(auto_now_add=True)
    """ When the object was created """
    
    modified = models.DateTimeField(auto_now=True)
    """ updated on modification """
   
    title = models.CharField(max_length=255)
    """ A descriptive title for the procedure. """
   
    author = models.CharField(max_length=255)
    """ The author of the procedure """
    
    description = models.TextField()
    """ Additional narrative information about the procedure. """
    
    version = models.CharField(max_length=255, default="1.0")
    """ The version string for this instance """
    
    src = models.FileField(upload_to='core/procedure', blank=True)
    """ File storage location for the procedure """

    voided = models.BooleanField(default=False)

    def __unicode__(self):
        return "%s %s" % (self.title, self.version)

