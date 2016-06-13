from django.forms import widgets

__all__ = [ 'AgeInput',
            'NumberInput',
            'DateSelectorInput',
            'DateTimeSelectorInput',
          ]

class NumberInput(widgets.TextInput):
    input_type="number"

class AgeInput(NumberInput):
    input_max=120
    input_min=0
    input_step=1    
    
class DateSelectorInput(widgets.DateInput):
    input_type="date"
    
class DateTimeSelectorInput(widgets.DateTimeInput):
    input_type="date"
    