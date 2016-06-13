"""
The observation model for the Sana data engine.

:Authors: Sana dev team
:Version: 2.0
"""

from django.db import models

from django.contrib.auth.models import User
from mds.api.utils import make_uuid

class Observer(models.Model):
    """ The user who executes the Procedure and collects the Observations """

    class Meta:
        app_label = "core"
        
    uuid = models.SlugField(max_length=36, unique=True, default=make_uuid, editable=False)
    """ A universally unique identifier """
    
    created = models.DateTimeField(auto_now_add=True)
    """ When the object was created """
    
    modified = models.DateTimeField(auto_now=True)
    """ updated on modification """

    user = models.OneToOneField(User, unique=True)
    """ A universally unique identifier. See  """

    voided = models.BooleanField(default=False)

    def __unicode__(self):
        return unicode(self.user)
