'''
:Authors: Sana Dev Team
:Version: 2.0
'''
import logging
from datetime import datetime
from django import forms
from django.forms.extras.widgets import SelectDateWidget
from  django.forms.widgets import PasswordInput

from django.contrib.auth.models import User

from extra_views import InlineFormSet

from mds.core.models import *
from mds.core.widgets import *
from mds.tasks.models import *

__all__ = [
    "ProcedureForm",
    "EmptyEncounterForm",
    "EncounterTaskForm",
    "AllowReadonly",
    "AllowReadonlyForm",
    "AllowReadonlyModelForm",
    "SpanField",
    "UserInline",
    "UserForm",
    "ObserverForm",
    "LoginForm",
    ]

def subject_choice_list():
    subject_list = (
        (x.uuid, u"%s - %s, %s" % (x.system_id,x.family_name, x.given_name)) for x in Subject.objects.all().exclude(voided=True))
    return  subject_list

def concept_choice_list():
    try:
        concepts = [
            Concept.objects.get(pk=28),
            Concept.objects.get(pk=27),
            Concept.objects.get(pk=26),
            Concept.objects.get(pk=29),
        ]
    except:
        concepts = []
    return ((x.uuid, x.display_name) for x in concepts)

class EmptyEncounterForm(forms.ModelForm):
    class Meta:
        model = Encounter
        widgets = {
            "device":forms.HiddenInput(),
            "procedure":forms.HiddenInput(),
            "observer" :forms.HiddenInput(),
            "concept":forms.HiddenInput(),
        }

class EncounterTaskForm(forms.ModelForm):
    """ Visits assigned to surgical advocate post S/P
    """
    class Meta:
        model = EncounterTask
    subject = forms.ChoiceField(subject_choice_list(), label="Patient")
    procedure = forms.ChoiceField(((x.uuid,x.title) for x in Procedure.objects.exclude(uuid__iexact="303a113c-6345-413f-88cb-aa6c4be3a07d")))
    assigned_to = forms.ModelChoiceField(queryset=Observer.objects.all())
    concept = forms.ChoiceField(concept_choice_list(), label="Type")
    due_on = forms.DateTimeField(widget=DateTimeSelectorInput(format='%Y-%m-%d %H:%M'))
    started = forms.DateTimeField(widget=DateTimeSelectorInput(format='%Y-%m-%d %H:%M'))
    completed = forms.DateTimeField(widget=DateTimeSelectorInput(format='%Y-%m-%d %H:%M'))

class SpanField(forms.Field):
    '''A field which renders a value wrapped in a <span> tag.
    
    Requires use of specific form support. (see ReadonlyForm 
    or ReadonlyModelForm)
    '''
    
    def __init__(self, *args, **kwargs):
        kwargs['widget'] = kwargs.get('widget', SpanWidget)
        super(SpanField, self).__init__(*args, **kwargs)

class AllowReadonly(object):
    '''Base class for ReadonlyForm and ReadonlyModelForm which provides
    the meat of the features described in the docstings for those classes.
    '''

    class NewMeta:
        readonly = tuple()

    def __init__(self, *args, **kwargs):
        super(AllowReadonly, self).__init__(*args, **kwargs)
        readonly = self.NewMeta.readonly
        if not readonly:
            return
        for name, field in self.fields.items():
            if name in readonly:
                field.widget = SpanWidget()
            elif not isinstance(field, SpanField):
                continue
            field.widget.original_value = str(getattr(self.instance, name))

class AllowReadonlyForm(AllowReadonly, forms.Form):
    '''A form which provides the ability to specify certain fields as
    readonly, meaning that they will display their value as text wrapped
    with a <span> tag. The user is unable to edit them, and they are
    protected from POST data insertion attacks.
    
    The recommended usage is to place a NewMeta inner class on the
    form, with a readonly attribute which is a list or tuple of fields,
    similar to the fields and exclude attributes on the Meta inner class.
    
        class MyForm(ReadonlyForm):
            foo = forms.TextField()
            class NewMeta:
                readonly = ('foo',)
    '''
    pass

class AllowReadonlyModelForm(AllowReadonly, forms.ModelForm):
    '''A ModelForm which provides the ability to specify certain fields as
    readonly, meaning that they will display their value as text wrapped
    with a <span> tag. The user is unable to edit them, and they are
    protected from POST data insertion attacks.
    
    The recommended usage is to place a NewMeta inner class on the
    form, with a readonly attribute which is a list or tuple of fields,
    similar to the fields and exclude attributes on the Meta inner class.
    
        class Foo(models.Model):
            bar = models.CharField(max_length=24)

        class MyForm(ReadonlyModelForm):
            class Meta:
                model = Foo
            class NewMeta:
                readonly = ('bar',)
    '''
    pass

class ProcedureForm(AllowReadonlyModelForm):
    class Meta:
        model = Procedure
    class NewMeta:
        readonly = ['uuid','created',]

class UserInline(InlineFormSet):
    model = User

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username','password', "first_name", 'last_name',)
        widgets = (
            {'password': forms.PasswordInput(attrs={
                "autocomplete":"off",
                "type":'password'}) },
            {'username': forms.TextInput(attrs={"autocomplete":"off"}) },
        )
        
class LoginForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username','password')

class BlankUserForm(UserForm):

    def __init__(self,**kwargs):
        if kwargs.get('instance',None):
            kwargs['instance'] = None
        if kwargs.get('data',None):
            kwargs['data'] = None
            kwargs['data'] = None
        UserForm.__init__(self, **kwargs)

class ObserverForm(forms.ModelForm):
    class Meta:
        model =User
