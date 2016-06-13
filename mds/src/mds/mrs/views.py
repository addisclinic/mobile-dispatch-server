import cjson
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django import forms
from django.conf import settings
from django.core.paginator import Paginator
from django.template import RequestContext 

from .models import RequestLog, Notification

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


def list_notifications(request):
    """Queries the db for all notifications"""
    notifications = Notification.objects.all()
    return render_to_response('notifications.html',
                              {'notifications': notifications})

def log_list(request):
    query = dict(request.GET.items())
    start = int(query.get('start', 1))
    limit = int(query.get('limit', 20))
    objects = RequestLog.objects.all().filter().order_by('-created')
    paginator = Paginator(objects, limit, allow_empty_first_page=True)
    objs = []
    for p in paginator.page(start).object_list.all():
        obj = p.get_representation(rep = 'full')
        m = obj.pop('message')
        try:
            obj['message'] = cjson.decode(m,True)
            print 'decoded'
        except:
            obj['message'] = m
        objs.append(obj)
    data = {'objects': objs,
            'limit': limit,
            'start': start,
            "rate": int(query.get('refresh', 5)),
            'range': range(1, paginator.num_pages + 1),
            "version": settings.API_VERSION }
    return render_to_response('logging/list.html', RequestContext(request,data))

def log_detail(request, uuid):
    log = RequestLog.objects.get(uuid=uuid)
    try:
        print type(log.messages)
        
        for x in log.messages:
            x['message'] = cjson.decode(x)
            print x['message']
    except:
        data = log.message
    message = {'id': uuid, 'data': data }
    return HttpResponse(cjson.encode(message))

def home(request):
    """Top level url
    
    Displays ::
    
        Sanamobile MDS : Online
    """
    return HttpResponse('Sanamobile MDS : Online')

