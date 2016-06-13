from django import forms

from .models import *

__all__ = [ 'EncounterTaskForm',
            'ObservationTaskForm']

class EncounterTaskForm(forms.ModelForm):
    class Meta:
        model = EncounterTask

class ObservationTaskForm(forms.ModelForm):
    class Meta:
        model = ObservationTask
