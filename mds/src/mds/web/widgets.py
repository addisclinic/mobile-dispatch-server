from django.forms import widgets
from django import forms
from django.utils.safestring import mark_safe

__all__ = [
    "hide_if_initialized",
    "SpanWidget",
    ]
    
def hide_if_initialized(form, field):
    if field:
        widget = forms.HiddenInput()
    else:
        widget = field.widget
    return widget
    

class SpanWidget(forms.Widget):
    '''Renders a value wrapped in a <span> tag.
    
    Requires use of specific form support. (see ReadonlyForm 
    or ReadonlyModelForm)
    '''

    def render(self, name, value, attrs=None):
        final_attrs = self.build_attrs(attrs, name=name)
        return mark_safe(u'<span%s >%s</span>' % (
            forms.util.flatatt(final_attrs), self.original_value))

    def value_from_datadict(self, data, files, name):
        return self.original_value
