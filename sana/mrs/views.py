import urllib
import telnetlib
import logging

from models import BinaryResource
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django import forms

from sana.mrs.openmrs import sendToOpenMRS
from sana.mrs.util import enable_logging
from sana.mrs.models import Notification

def chunk( seq, size, pad=None ):
    """Slice a list into consecutive disjoint 'chunks' of
    length equal to size. The last chunk is padded if necessary.

    Example: ::

        >>> list(chunk(range(1,10),3))
            [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        >>> list(chunk(range(1,9),3))
            [[1, 2, 3], [4, 5, 6], [7, 8, None]]
        >>> list(chunk(range(1,8),3))
            [[1, 2, 3], [4, 5, 6], [7, None, None]]
        >>> list(chunk(range(1,10),1))
            [[1], [2], [3], [4], [5], [6], [7], [8], [9]]
        >>> list(chunk(range(1,10),9))
            [[1, 2, 3, 4, 5, 6, 7, 8, 9]]
        >>> for X in chunk([],3): print X
        >>>

    Parmeters:
        seq
            The sequence to slice
        size
            The size of each chunk
        pad
            The size to pad each chunk to.
    """
    n = len(seq)
    mod = n % size
    for i in xrange(0, n-mod, size):
        yield seq[i:i+size]
    if mod:
        padding = [pad] * (size-mod)
        yield seq[-mod:] + padding

class FakeProcedureSubmitForm(forms.Form):
    """Encounter form for testing"""
    responses = forms.CharField(required=True,
                                help_text='question,answer,question,answer,..')
    procedure_id = forms.IntegerField(required=True, help_text="integers only")
    phone_id = forms.CharField(max_length=255)
    patient_id = forms.CharField(max_length=255)
    #data = forms.FileField(required=True)

def procedure_submit(request):
    """For testing encounter submission"""
    upload = request.FILES.get('data', None)
    print upload

    if request.method == 'POST' and upload is not None:
        form = FakeProcedureSubmitForm(request.POST)
    else:
        form = FakeProcedureSubmitForm()

    if form.is_valid():
        print "valid"
        print form.cleaned_data

        phoneId = form.cleaned_data['phone_id']
        patientId = form.cleaned_data['patient_id']
        procedureId = form.cleaned_data['procedure_id']
        responses = form.cleaned_data['responses']


        binary = BinaryResource(element_id='test',
                       content_type='',
                       procedure=procedureId)
        binary.data.save(upload.name, upload)
        binary.save()

        qas = {}
        for q,a in chunk(responses.split(','),2, pad=''):
            qas[q] = a

        if procedureId == 1:
            procedureId = "Diagnose Cervical Cancer"
        sendToOpenMRS(patientId, phoneId, procedureId, str(binary.data.path), qas)


    return render_to_response("procedure_submit.html",
                              {'form': form})

def list_notifications(request):
    """Queries the db for all notifiactions"""
    notifications = Notification.objects.all()
    return render_to_response('notifications.html',
                              {'notifications': notifications})

def home(request):
    """Top level url

    Displays ::

        Sanamobile MDS : Online
    """
    return HttpResponse('Sanamobile MDS : Online')



