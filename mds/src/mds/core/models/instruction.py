""" Represents a single step within a Procedure.

:Authors: Sana dev team
:Version: 2.0
"""

from django.db import models
from mds.api.utils import make_uuid

## ?Procedure step. First iteration
class Instruction(models.Model):
    
    class Meta:
        app_label = "core"
    uuid = models.SlugField(max_length=36, unique=True, default=make_uuid, 
        editable=False)

    concept = models.ForeignKey('Concept', to_field='uuid')
    ''' Contextual information about the instruction '''
    
    predicate = models.CharField(max_length=64)
    ''' The predicate logic used for this instruction within a decision tree.'''
    
    algorithm = models.CharField(max_length=64)
    ''' The name of an algorithm used to calculate a score for the instruction.'''
    
    compound = models.BooleanField(default=False)
    ''' True if this Instruction has child instructions. '''

    boolean_operator = models.CharField(max_length=64, blank=True)
    ''' The logical operator to apply when evaluating children if compound.'''

    voided = models.BooleanField(default=False)