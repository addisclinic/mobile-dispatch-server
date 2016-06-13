"""Lexicon models for the core data layer.

:Authors: Sana dev team
:Version: 2.0
"""

from django.conf import settings
from django.db import models

from mds.api.utils import make_uuid

class Concept(models.Model):
    """ A unit of knowledge."""
    
    class Meta:
        app_label = "core"
        
    def __unicode__(self):
        return self.name
    
    uuid = models.SlugField(max_length=36, unique=True, default=make_uuid, editable=False)
    """ A universally unique identifier """
    
    created = models.DateTimeField(auto_now_add=True)
    """ When the object was created """
    
    modified = models.DateTimeField(auto_now=True)
    """ updated on modification """
    
    name = models.CharField(max_length=255, unique=True)
    """ A short unique name."""
    
    display_name = models.CharField(max_length=255, blank=True)
    """ Optional descriptive name or text. """
    
    description = models.CharField(max_length=255, blank=True)
    
    conceptclass = models.CharField(max_length=255, blank=True)
    
    datatype = models.CharField(max_length=64,
                                choices=((x,x) for x in settings.DATATYPES),
                                default="string")
    """ The data class, i.e. string, int, etc. """
    
    mimetype = models.CharField(max_length=64,
                                choices=settings.MIMETYPES,
                                default="text/plain")
    
    constraint = models.CharField(max_length=255, blank=True)
    
    voided = models.BooleanField(default=False)
    
    @property
    def is_complex(self):
        return self.datatype == 'complex' or self.datatype == 'blob'
    """ True if this concept requires file storage when used for values """

    def add_relationship(self, concept, category):    
        relationship, _ = Relationship.objects.get_or_create(from_concept=self,        
                                                               to_concept=concept,        
                                                               category=category)    
        return relationship
    
    def remove_relationship(self, concept, category):    
        Relationship.objects.filter(from_concept=self,         
                                    to_concept=concept,        
                                    category=category).delete()    
        return

    def get_relationships(self, category):
        return self.relationships.filter(
            to_concept__category=category,         
            to_concept__from_concept=self)

    def get_related_to(self, category):    
        return self.related_to.filter(        
            from_concept__category=category,         
            from_concept__to_concept=self)

class RelationshipCategory(models.Model):
    """ A type of relationship between two concepts 
    """
    class Meta:
        app_label = "core"
        
    def __unicode__(self):
        return self.name
    
    uuid = models.SlugField(max_length=36, unique=True, default=make_uuid, editable=False)
    """ A universally unique identifier """
    
    created = models.DateTimeField(auto_now_add=True)
    """ When the object was created """
    
    modified = models.DateTimeField(auto_now=True)
    """ updated on modification """
                    
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=512, blank=True)
    restriction = models.CharField(max_length=512, blank=True)

class Relationship(models.Model):
    """ A relationship between two concept instances 
    """
    class Meta:
        app_label = "core"
    uuid = models.SlugField(max_length=36, unique=True, default=make_uuid, editable=False)
    """ A universally unique identifier """
    
    created = models.DateTimeField(auto_now_add=True)
    """ When the object was created """
    
    modified = models.DateTimeField(auto_now=True)
    """ updated on modification """    
    from_concept = models.ForeignKey('Concept', 
                            related_name='concept_related_from',
                            to_field='uuid')
    to_concept = models.ForeignKey('Concept', 
                            related_name="concept_related_to",
                            to_field='uuid')
    category = models.ForeignKey('RelationshipCategory')
    
    def __unicode__(self):
        return u'{to} {relationship} {from}'.format(self.to_concept.name, 
                                                    self.from_conept.name, 
                                                    self.category.name)

