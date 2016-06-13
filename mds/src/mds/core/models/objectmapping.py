'''
@author: Sana Development
'''
from django.db import models

from . import Concept, Device, Encounter, Observer, Observation

_models = {"Concept": Concept, 
           "Device": Device, 
           "Encounter": Encounter,
           "Observer": Observer, 
           "Observation": Observation}
_choices = ((k,v.name) for k,v in _models.items())

class ObjectMapping(models.Model):
    ''' Mapping from internal to external unique identiifer
    '''
    class Meta:
        app_label = "core"
        
    
    object_model = models.CharField(())
    """ The Model class of the object. """
    
    object_uuid = models.SlugField(max_length=36, unique=True, editable=False)
    """ The object's internal unique identifier. """
    
    external_domain = models.CharField()
    """ The domain where the external  unique identifier is defined """
    
    external_uuid = models.CharField()
    """ The value of the external unique identifier. """
    
    @property
    def object(self):
        klazz = _models[self.object_model]
        return klazz.objects.get(uuid=self.object_uuid)