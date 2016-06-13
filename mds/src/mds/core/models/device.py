""" An entity that  acts as a tool for data collection.

:Authors: Sana dev team
:Version: 2.0
"""

from django.db import models

from mds.api.utils import make_uuid

class Device(models.Model):
    """ The entity which is used to collect the data """
    
    class Meta:
        app_label = "core"
        
    uuid = models.SlugField(max_length=36, unique=True, default=make_uuid, editable=False)
    """ A universally unique identifier """
    
    created = models.DateTimeField(auto_now_add=True)
    """ When the object was created """
    
    modified = models.DateTimeField(auto_now=True)
    """ updated on modification """
           
    name = models.CharField(max_length=36)
    """ A display name """

    voided = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name
