import urllib
import telnetlib
import logging
import cjson

from models import BinaryResource
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django import forms
from django.contrib.auth import authenticate, login

from sana.mrs.openmrs import sendToOpenMRS
from sana.mrs.util import enable_logging
from sana.mrs.models import Notification
from sana.mrs.util import enable_logging

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

def notification_submit(request):
    return render_to_response("notification_submit.html")

@enable_logging
def list_notifications(request):
    """For synching notifications with mobile clients.

    Request Params
        username
            A valid username.
        password
            A valid password.

    Parameters:
        request
            A client request for patient list
    """
    logging.info("entering notification list proc")

    username = request.REQUEST.get('username',None)
    password = request.REQUEST.get('password',None)
    user = authenticate(username=username, password=password)
    if user is not None:
        try:
            data = Notification.objects.all()
            logging.info("we finished getting the notification list")
            response = {'status': 'SUCCESS',
                'data': [cjson.decode(d.to_json()) for d in data],
            }
        except Exception, e:
            et, val, tb = sys.exc_info()
            trace = traceback.format_tb(tb)
            error = "Exception : %s %s %s" % (et, val, trace[0])
            for tbm in trace:
                logging.error(tbm)
            logging.error("Got exception while fetching notification list: %s" % e)
            response = {
                'status': 'FAILURE',
                'data': "Problem while getting notification list: %s" % e,
            }
    else:
        logging.error('User not authenticated')
        response = {
            'status': 'FAILURE',
            'data': 'User not authenticated',
        }
    return HttpResponse(cjson.encode(response), content_type=("application/json; charset=utf-8"))

def home(request):
    """Top level url

    Displays ::

        Sanamobile MDS : Online
    """
    return HttpResponse('Sanamobile MDS : Online')



