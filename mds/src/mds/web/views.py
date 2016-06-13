import cjson
import logging

from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse

from django import forms
from django.forms.models import modelformset_factory, modelform_factory
from django.db.models import ForeignKey, FileField, ImageField, DateField, DateTimeField

from django.shortcuts import render_to_response,redirect
from django.template import RequestContext
from django.template.response import TemplateResponse 
from django.views.generic import DetailView, ListView, CreateView, UpdateView
from django.views.generic.detail import *
from django.utils.translation import ugettext_lazy as _

from extra_views import CreateWithInlinesView, UpdateWithInlinesView
from django.contrib.auth.models import User

from mds.api import version
from mds.api.responses import JSONResponse
from mds.core.models import *
from .forms import *
from mds.core.widgets import *
from mds.web.generic.filtering import FilterMixin
from .generic.sorting import SortMixin
from mds.tasks.models import *
from .portal import site as portal_site

def login(request,*args,**kwargs):
    if request.method == "POST":
        form = {}
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        redirect_to = request.REQUEST.get("next", '')
        next_page = redirect_to if redirect_to else reverse("web:portal")
        if user is None:
            return TemplateResponse(request,
                'web/login.html',
                {
                    'form': LoginForm(),
                    'next': next_page
                })
            
        else:
            auth_login(request, user)
            return HttpResponseRedirect(next_page)
    else:
        form = modelform_factory(User)
        return TemplateResponse(request,
            'web/login.html',
            {
                'form': LoginForm(),
            })

def logout(request):
    auth_logout(request)
    url = reverse('web:login')
    return redirect(url)

def home(request):
    """Top level url
    
    Displays ::
        {"status": "SUCCESS | FAIL", 
         "code",  "200|401",
         "message": mds.api.version() }
    """
    username = request.REQUEST.get('username', 'empty')
    password = request.REQUEST.get('password','empty')
    user = authenticate(username=username, password=password)
    if user is not None:
        return HttpResponse(cjson.encode( {
               'status':'SUCCESS',
               'code':200,
               'message': version()}))
    else:
        message = unicode('UNAUTHORIZED:Invalid credentials!')
        logging.warn(message)
        logging.debug(u'User' + username)
        return HttpResponse(cjson.encode({
                'status':'FAIL',
                'code':401, 
                'message': message}))

def mobile_authenticate(request,**kwargs):
    username = request.REQUEST.get('username', 'empty')
    password = request.REQUEST.get('password','empty')
    user = authenticate(username=username, password=password)
    observer = None
    role = 0
    try:
        observer = Observer.objects.get(user__username=username)
        role = 1 if user.is_superuser else 2
    except:
        pass
    if user is not None and observer is not None:
        return HttpResponse(cjson.encode( {
               'status':'SUCCESS',
               'code':200,
               'message': [
                    {
                        "uuid": observer.uuid,
                        "role": role,
                    }
                ]}))
    else:
        message = unicode('UNAUTHORIZED:Invalid credentials!')
        logging.warn(message)
        logging.debug(u'User' + username)
        return HttpResponse(cjson.encode({
                'status':'FAIL',
                'code':401, 
                'message': []}))

class _metadata(object):
    def __init__(self,request):
        self.params = request.COOKIES
        self.flavor = self.params.get("flavor",None)
        self.debug = []
        self.errors = []
        self.mode = self.params.get("mode","normal")
        if self.mode == "verbose":
            self.debug.append("mode: %s" % self.mode)
            for k,v in request.session.items():
                self.debug.append("%s : %s" %(k,v))
        else:
            self.debug.append("Nothing to see here.")

    @property
    def messages(self):
            return self.debug

@login_required(login_url='/login/')
def web_root(request, **kwargs):
    from mds.core import models as objects
    metadata = _metadata(request)
    return render_to_response("web/index.html", 
                              context_instance=RequestContext(request,{
                              'flavor': metadata.flavor,
                              'errors': metadata.errors,
                              'messages' : metadata.messages,
                              'models' : objects.__all__
                            }))

def registration(request, **kwargs):
    metadata = _metadata(request)
    return render_to_response("web/registration.html", 
                              context_instance=RequestContext(request,{
                              'form':  SurgicalSubjectForm(),
                              'flavor': metadata.flavor,
                              'errors': metadata.errors,
                              'messages' : metadata.messages
                               }))

@login_required(login_url='/mds/login/')
def encounter_task(request, **kwargs):
    flavor = kwargs.get('flavor',None) if kwargs else None
    params = request.COOKIES
    data = {}
    debug = []
    errors = []

    tmpl = "web/etask.html"
    # Get the request cookies and check for values to preload
    mode = params.get("mode","normal")
    debug.append(u'mode: %s' % mode)
    # Should use this to track IP's?
    device = params.get('device', None)
    if device:
        device = Device.objects.get(uuid=device)
    data['device'] = device
    # Check for a preassigned subject
    subject = params.get('subject', None)
    new_patient = bool(params.get("new_patient", False))
    if subject:
        subject = Subject.objects.get(uuid=subject)
        
    else:
        if mode and mode == "test":
            subject = Subject.objects.get(uuid="e7d4bdd8-2cfa-400c-b4bc-330fcd2497fc")
    data["subject"] = subject
    
    form = EncounterTaskForm(initial=data)
    return render_to_response(tmpl, 
                              context_instance=RequestContext( request, 
                                {
                                 'form':form,
                                 'flavor': flavor,
                                 'errors': errors,
                                 'debug' : debug
                                })
                             )

@login_required(login_url='/mds/login/')
def edit_encounter_task(request, uuid, **kwargs):
    if(uuid):
        try:
            task = EncounterTask.objects.get(uuid=uuid)
        except:
            return encounter_task(request)
    flavor = kwargs.get('flavor',None) if kwargs else None
    params = request.COOKIES
    data = {}
    debug = []
    errors = []

    tmpl = "web/etask.html"
    # Get the request cookies and check for values to preload
    mode = params.get("mode","normal")
    debug.append(u'mode: %s' % mode)
    # Should use this to track IP's?
    device = params.get('device', None)
    if device:
        device = Device.objects.get(uuid=device)
    data['device'] = device
    task = None
    # Check for a preassigned subject

    
    form = EncounterTaskForm(task)
    return render_to_response(tmpl, 
                              context_instance=RequestContext( request, 
                                {
                                 'form':form,
                                 'flavor': flavor,
                                 'errors': errors,
                                 'debug' : debug
                                })
                             )
@login_required(login_url='/mds/login/')
def web_encounter(request, **kwargs):
    _cookies = request.COOKIES
    params = request.COOKIES
    data = {}
    errors = []
    debug = []

    form_klazz = EmptyEncounterForm

    # Get the request cookies and check for values to preload
    mode = params.get("mode","normal")

    # Allow the flavor to be sent as kw or cookie
    flavor = kwargs.get('flavor',None) if kwargs else None
    if not flavor:
        flavor = _cookies.get("flavor",None)

    # Should use this to track IP's?
    device = params.get('device', "2fc0a9f7-384b-4d97-8c1c-aa08f0e12105")
    if device:
        device = Device.objects.get(uuid=device)
    data["device"] = device

    # Defaults to generic encounter
    concept = params.get('concept', "521b0825-14c9-49e5-a95e-462a01e2ae05")
    if concept:
        concept = Concept.objects.get(uuid=concept)
    data["concept"] = concept

    # Defaults to Intake procedure for now
    # TODO move to setting?
    procedure = params.get('procedure', "303a113c-6345-413f-88cb-aa6c4be3a07d")
    if procedure:
        procedure = Procedure.objects.get(uuid=procedure)
    data["procedure"] = procedure

    # Check for a preassigned subject
    subject = params.get('subject', None)
    if subject:
        subject = Subject.objects.get(uuid=subject)
    else:
        if mode and mode == "test":
            subject = Subject.objects.get(uuid="e7d4bdd8-2cfa-400c-b4bc-330fcd2497fc")
    data["subject"] = subject

    # Check that we have an observer
    observer = Observer.objects.get(user__username=request.user)
    data['observer'] = observer

    form_klazz = _procedure_forms.get(procedure.uuid, EmptyEncounterForm) if procedure else form_klazz
    try:
        form = form_klazz(initial=data)
        if mode == "verbose":
            debug.append("Initial data:")
            for k,v in data.items():
                debug.append(u"  %s : %s" % (k,v))
        else:
            debug.append("Nothing to see here")
            for k,v in data.items():
                debug.append(u"  %s : %s" % (k,v))
    except:
        form = form_klazz()
        errors.append(u"Problem with initializing form with data")
        errors.append(u"%s" % form_klazz)
        for k,v in data.items():
            errors.append(u"%s : %s" % (k,v))

    return render_to_response("web/encounter_form.html", 
                              context_instance=RequestContext( request, 
                                {
                                 'form': form,
                                 'flavor': flavor,
                                 'errors': errors,
                                 'messages' : debug,
                                 'debug' : debug
                                })
                             )

@login_required(login_url='/mds/login/')
def task_list(request):
    query = dict(request.GET.items())
    page = int(query.get('page', 1))
    page_size = int(query.get('page_size', 20))
    prange =  range(0, 1)

    task_list = EncounterTask.objects.all()
    paginator = Paginator(task_list, page_size)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        tasks = paginator.page(page)
    except (EmptyPage, InvalidPage):
        tasks = paginator.page(paginator.num_pages)
    prange = range(1,paginator.num_pages + 1)
    return render_to_response("web/etask_list.html", 
                              context_instance=RequestContext( request, 
                                {
                                 'tasks':tasks.object_list,
                                 'range':prange,
                                 'page': page,
                                }
                              )
    )

def _list(request,*args,**kwargs):
    query = dict(request.GET.items())
    start = int(query.pop('start', 1))
    limit = int(query.pop('limit', 20))
    level = int(query.pop('level', 0))
    if level and level > 0:
        objects = Event.objects.filter(level=level).order_by('-created')
    else:
        objects = Event.objects.filter(**query).order_by('-created')
    #objects = objects.filter(**query).order_by('-created')
   
    #if query:
    #    paginator = Paginator(objects.filter(**query)), limit, allow_empty_first_page=True)
    #else:
    #    
    paginator = Paginator(objects, limit, allow_empty_first_page=True)
    objs = []
    for p in paginator.page(start).object_list:#.all():
        #p.full_clean()
        #obj = p.to_python()
        #m = obj.pop('message')
        m = p.messages
        try:
            #obj['message'] = cjson.decode(m,True)
            p.messages = cjson.decode(m,True)
        except:
            pass
            #obj['message'] = m
        objs.append(p)
    data = {'objects': objs,
            'limit': limit,
            'start': start,
            "rate": int(query.get('refresh', 5)),
            'range': range(1, paginator.num_pages + 1),
            "version": settings.API_VERSION }
    return data

def logs(request,*args,**kwargs):
    data = _list(request)
    data['portal'] = portal_site
    return render_to_response('web/logs.html', RequestContext(request,data))

def log_list(request):
    data = _list(request)
    return render_to_response('web/log_list.html', RequestContext(request,data))

def log_report(request):
    post = dict(request.POST.items())
    selected = []
    for k,v in post.items():
        if v:
            selected.append(k)
    objects = Event.objects.all().filter(uuid__in=selected)
    return JSONResponse(objects)

def log_detail(request, uuid):
    log = Event.objects.get(uuid=uuid)
    data = []
    messages = cjson.decode(log.messages)
    for m in messages:
        try:
            m['message'] = cjson.decode(m['message'])
        except:
            pass
        
        data.append(m)
#           m['message']  = cjson.decode(m['message'])
#            data.append(m)
#        except:
            
            
    message = { 'message': data, 'uuid': uuid, }
    return HttpResponse(cjson.encode(message))

def log(request,*args,**kwargs):
    query = dict(request.GET.items())
    page = int(query.get('page', 1))
    page_size = int(query.get('page_size', 20))
    
    data = {'object_list': {},
            'page_range': range(0, 1),
            'page_size': page_size,
            'page': page,
            "rate": int(query.get('refresh', 5)) }
    return render_to_response('logging/index.html', RequestContext(request,data))


########################################################################
# Class based views
########################################################################
#class @ListView(ListView):
#    model = @
#    template_name = "web/@_list.html"
#
#class @CreateView(CreateView):
#    model = @
#    template_name = "web/@_edit.html"
    

_core = [
    Concept,
    Device,
    Encounter,
    Location,
    Notification, 
    Observation, 
    Observer,
    Procedure,
    Subject,
]

_tasks = [
    EncounterTask,
]

class ModelListMixin(SortMixin):
    template_name = "web/form.html"
    exclude = ()
    _fields = []
    default_sort_params = ('created', 'asc')
    
    def __init__(self, *args, **kwargs):
        super(ModelListMixin,self)
        self._fields = self.field_names()
        if not hasattr(self,'form'):
            self.form = modelform_factory(self.model)
        if not hasattr(self,'exclude'):
            self.exclude = ()

    def field_names(self):
        if not getattr(self,'fields',None):
            return list(x.name for x in self.model._meta.fields)
        else:
            return self.fields

    def get_object_dict(self, obj):
        opts = obj._meta
        from django.utils.datastructures import SortedDict
        _obj = SortedDict()
        fields = SortedDict()
        for f in self._fields:
            #field = getattr(obj._meta, f, None)
            field = opts.get_field(f)
            data = {
                    'label_tag': f.replace("_"," "),
                    'is_link': False,
                    'value': getattr(obj, f),
                    'url': None,
                    'type': 'text',
            }
            if isinstance(field, ForeignKey):
                field_obj = getattr(obj,f)
                data['is_link'] = True
                data['url'] = u'/mds/web/{model}/{uuid}/'.format(
                    model=field_obj.__class__.__name__.lower(),
                    uuid=unicode(field_obj.id))
                data['type'] = 'object'
            elif isinstance(field, FileField):
                data['is_link'] = True
                data['url'] = u'/mds/media/{path}'.format(
                    path=unicode(getattr(obj, f)))
                data['type'] = 'file'
            elif isinstance(field, DateField):
                data['type'] = 'date'
            elif isinstance(field, DateTimeField):
                data['type'] = 'date'
            fields[f] = data
        _obj['fields'] = fields
        _obj['id'] = obj.id
        _obj['repr'] = unicode(obj)
        return _obj

    def get_context_data(self, **kwargs):
        context = super(ModelListMixin, self).get_context_data(**kwargs)
        context['model'] = self.model.__name__.lower()
        #context['form'] = self.form(self.object)
        context['fields'] = self._fields
        if context.has_key('object'):
            context['object_list'] = [context['object'],]
        context['objects'] = list(self.get_object_dict(x) for x in context['object_list'])
        #sort_by, order = self.get_sort_params()
        #context.update({'sort_by': sort_by, 'order': order})
        context['portal'] = portal_site
        return context

class ModelMixin(object):
    template_name = "web/form.html"
    
    def __init__(self, *args, **kwargs):
        super(ModelMixin,self)
    #    if not hasattr(self,'fields'):
    #        self.fields = self.get_default_model_fields()
    #    if not hasattr(self,'form'):
    #        self.form =  modelform_factory(self.model, fields=self.fields)

    def get_context_data(self, **kwargs):
        context = super(ModelMixin, self).get_context_data(**kwargs)
        context['model'] = self.model.__name__.lower()
        return context
        
class ModelFormMixin(object):
    template_name = "web/form.html"
    default_sort_params = ('created', 'asc')
    exclude = ()
    _fields = []
    success_url_format = "/{app}/{model}/%(id)s/"
    app = 'mds.web'
    
    def __init__(self, *args, **kwargs):
        super(ModelFormMixin,self)
        #if not hasattr(self,'fields'):
        #    self.fields = self.get_default_model_fields()
        self._fields = self.field_names()
        if not hasattr(self,'form'):
            self.form = modelform_factory(self.model)
        if not hasattr(self,'exclude'):
            self.exclude = ()
        _model = getattr(self,"model").__name__.lower()
        _app = getattr(self,'app').replace(".","/")
        setattr(self,'success_url', 
                self.success_url_format.format(app=_app,model=_model))

    def field_names(self):
        if not getattr(self,'fields',None):
            return list(x.name for x in self.model._meta.fields)
        else:
            return self.fields

    def get_field_list(self, obj):
        from django.utils.datastructures import SortedDict
        form = self.form(instance=obj)
        opts = obj._meta
        fields = SortedDict()
        objs = SortedDict()
        for field in self._fields:
            _obj = {}
            if not field.name in self.exclude:
                data = {
                    'name': field.name,
                    'is_link': False,
                    'value': getattr(obj,field.name),
                    'link': None,
                    'secure': False,
                }
                if isinstance(field.widget, forms.PasswordInput):
                    data['secure'] = True
                if isinstance(field, ForeignKey):
                    data['is_link'] = True
                    data['link'] = u'/mds/web/{model}/{uuid}/'.format(
                        model=field.model,
                        uuid=unicode(getattr(obj,field.name)
                        ))
                elif isinstance(field, FileField):
                    data['is_link'] = True
                    data['link'] = u'/mds/media/{path}'.format(
                        path=unicode(getattr(obj,field.name)
                        ))
                _obj[field.name] = data
                objs.append(_obj)
        return tuple(fields)

    def get_object_dict(self, obj):
        opts = obj._meta
        from django.utils.datastructures import SortedDict
        _obj = SortedDict()
        fields = SortedDict()
        for f in self._fields:
            #_field = field.name 
            #for _field  in self._fields:
            #if field.name in self._fields:
            field = getattr(opts, f, None)
            _field = None
            for x in obj._meta.fields:
                if x.name == f:
                    _field = x
            #_field = type(f)
            data = {
                    'label_tag': f.replace("_"," "),
                    'is_link': False,
                    'value': getattr(obj, f),
                    'url': None,
                    'type': _field,
                    'secure': False,
                    'input_type': 'text',
            }
            if isinstance(_field, ForeignKey):
                data['is_link'] = True
                data['url'] = u'/mds/web/{model}/{uuid}/'.format(
                    model= f.lower(), 
                    uuid=unicode(getattr(obj, f).id))
                data['type'] = 'ref'
            elif isinstance(_field, FileField):
                data['is_link'] = True
                data['url'] = u'/mds/media/{path}'.format(
                    path=unicode(getattr(obj, f)))
                data['type'] = 'file'
            elif isinstance(_field, DateField):
                data['type'] = 'date'
            elif isinstance(_field, DateTimeField):
                data['type'] = 'date'
            fields[f] = data
        _obj['fields'] = fields
        _obj['id'] = obj.id
        _obj['repr'] = unicode(obj)
        return _obj

    def get_context_data(self, **kwargs):
        context = super(ModelFormMixin, self).get_context_data(**kwargs)
        context['model'] = self.model.__name__.lower()
        #context['form'] = self.form(self.object)
        context['fields'] = self._fields
        if context.has_key('object'):
            context['objects'] = [self.get_object_dict(context['object']),]
        if context.has_key('object_list'):
            context['objects'] = list(self.get_object_dict(x) for x in context['object_list'])
        context['portal'] = portal_site
        return context

class ModelSuccessMixin(SuccessMessageMixin):
    success_message = "%(model)s: %(uuid)s was updated successfully"

    def get_success_message(self, cleaned_data):
        klazz = getattr(self,'model',None)
        if klazz:
            klazz = klazz.__name__
        else:
            klazz = _('Object')
        data = {
            'model': klazz,
            'uuid' : self.object.uuid
            }
        return self.success_message % (data)

# Concepts
class UserListView(ModelListMixin, ListView):
    model = User
    template_name = "web/list.html"
    fields = ('username','last_name','first_name',)
    paginate_by=10
    default_sort_params = ('username','last_name',)

class UserCreateView(SuccessMessageMixin,CreateView):
    model = User
    template_name = "web/form_user_new.html"
    form_class = UserForm
    success_message = "User: %(username)s was created successfully"

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(cleaned_data)
        
    def get_context_data(self, **kwargs):
        context = super(UserCreateView, self).get_context_data(**kwargs)
        context['model'] = self.model.__name__.lower()
        context['portal'] = portal_site
        return context

class UserUpdateView(ModelFormMixin, SuccessMessageMixin, UpdateView):
    model = User
    template_name = 'web/form_user.html'
    form_class = UserForm

    success_message = "User: %(username)s was updated successfully"

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(cleaned_data)

class UserDetailView(ModelFormMixin,DetailView):
    model = User
    template_name = 'web/detail.html'
    context_object_name = 'user'
    slug_field = 'uuid'
    fields = ('username','last_name','first_name','email')

# Concepts
class ConceptListView(ModelListMixin, ListView):
    model = Concept
    template_name = "web/list.html"
    fields = ('created', 'name', 'description', 'voided')
    paginate_by=10

class ConceptCreateView(ModelFormMixin,SuccessMessageMixin,CreateView):
    model = Concept
    template_name = "web/form_new.html"

class ConceptUpdateView(ModelFormMixin, SuccessMessageMixin, UpdateView):
    model = Concept
    template_name = 'web/form.html'
    success_message = _("Concept: %(name)s was updated successfully")
    
    def get_success_message(self, cleaned_data):
        return self.success_message % dict(cleaned_data)
        
class ConceptDetailView(ModelFormMixin,DetailView):
    model = Concept
    template_name = 'web/detail.html'
    context_object_name = 'concept'
    slug_field = 'uuid'

# Devices
class DeviceListView(ModelListMixin, ListView):
    model = Device
    template_name = "web/list.html"
    fields = ('created','name','voided',)
    paginate_by=10

class DeviceCreateView(ModelFormMixin,CreateView):
    model = Device
    template_name = "web/form_new.html"

class DeviceUpdateView(ModelFormMixin, UpdateView):
    model = Device
    template_name = 'web/form.html'

class DeviceDetailView(ModelFormMixin, DetailView):
    model = Device
    template_name = 'web/detail.html'
    context_object_name = 'device'
    slug_field = 'uuid'

# Encounters
class EncounterListView(ModelListMixin,ListView):
    model = Encounter
    template_name = "web/list.html"
    fields = ('created', 'procedure', 'subject')
    paginate_by=10
    
class EncounterCreateView(ModelFormMixin,CreateView):
    model = Encounter
    template_name = "web/form_new.html"

class EncounterUpdateView(ModelFormMixin, UpdateView):
    model = Encounter
    template_name = "web/form.html"

class EncounterDetailView(ModelFormMixin,DetailView):
    model = Encounter
    template_name = 'web/encounter_detail.html'
    context_object_name = 'encounter'
    slug_field = 'uuid'

# Locations
class LocationListView(ModelListMixin, ListView):
    model = Location
    template_name = "web/list.html"
    paginate_by=10
    default_sort_params = ('name', 'asc')
    fields = ('name','code',)
    
class LocationCreateView(ModelFormMixin,CreateView):
    model = Location
    template_name = "web/form_new.html"
    #success_url="/mds/web/location/%(id)s/"
    
class LocationUpdateView(ModelFormMixin, UpdateView):
    model = Location
    template_name = 'web/form.html'
    #success_url='/mds/web/location/%(id)s/'
    
class LocationDetailView(ModelFormMixin,DetailView):
    model = Location
    template_name = 'web/detail.html'
    context_object_name = 'location'
    slug_field = 'uuid'

# Observations
class ObservationListView(ModelListMixin, ListView):
    model = Observation
    template_name = "web/list.html"
    paginate_by=10
    fields = (
        'created',
        'encounter',
        'node',
        'concept',
        'value_text',
        'value_complex',
    )

class ObservationCreateView(ModelFormMixin,CreateView):
    model = Observation
    template_name = "web/form_new.html"

class ObservationUpdateView(ModelFormMixin, ModelSuccessMixin, UpdateView):
    model = Observation
    template_name = 'web/form.html'

class ObservationDetailView(ModelFormMixin,DetailView):
    model = Observation
    template_name = 'web/detail.html'
    context_object_name = 'observation'
    slug_field = 'uuid'

# Observers
class ObserverListView(ModelListMixin, ListView):
    model = Observer
    template_name = "web/list.html"
    paginate_by=10

class ObserverCreateView(ModelFormMixin,CreateView):
    model = Observer
    template_name = "web/form_new.html"
    
class ObserverUpdateView(ModelFormMixin, UpdateView):
    model = Observer
    template_name = 'web/form.html'

class ObserverDetailView(ModelFormMixin,DetailView):
    model = Observer
    template_name = 'web/detail.html'
    context_object_name = 'observer'
    slug_field = 'uuid'

# Procedures
class ProcedureListView(ModelListMixin, ListView):
    template_name = 'web/list.html'
    model = Procedure
    default_sort_params = ('title', 'asc')
    fields = ('title', 'version', 'author', 'src')#,'uuid')
    paginate_by=3

        
class ProcedureDetailView(ModelFormMixin,DetailView):
    model = Procedure
    template_name = 'web/detail.html'
    context_object_name = 'procedure'
    slug_field = 'uuid'
    
class ProcedureCreateView(ModelFormMixin,CreateView):
    model = Procedure
    template_name = "web/form_new.html"

class ProcedureUpdateView(ModelFormMixin, UpdateView):
    model = Procedure
    template_name = 'web/form.html'

class SubjectListView(ModelListMixin, ListView):
    model = Subject
    default_sort_params = ('system_id', 'asc')
    fields = ('created', 'system_id', 'family_name', 'given_name', 'gender', 'dob','voided')
    template_name = "web/list.html"
    paginate_by=10

class SubjectCreateView(ModelFormMixin,CreateView):
    model = Subject
    template_name = "web/form_new.html"

class SubjectUpdateView(ModelFormMixin, UpdateView):
    model = Subject
    template_name = 'web/form.html'

class SubjectDetailView(ModelFormMixin,DetailView):
    model = Subject
    template_name = 'web/detail.html'
    context_object_name = 'subject'
    slug_field = 'uuid'

class EncounterTaskListView(ModelListMixin, ListView):
    model = EncounterTask
    default_sort_params = ('due_on', 'asc')
    fields = ('due_on', 'subject')
    template_name = "web/list.html"
    paginate_by=10

class EncounterTaskCreateView(ModelFormMixin,CreateView):
    model = EncounterTask
    template_name = "web/form_new.html"
    form_class = EncounterTaskForm

class EncounterTaskUpdateView(ModelFormMixin, UpdateView):
    model = EncounterTask
    template_name = 'web/form.html'
    form_class = EncounterTaskForm

class EncounterTaskDetailView(ModelFormMixin,DetailView):
    model = EncounterTask
    template_name = 'web/detail.html'
    context_object_name = 'encountertask'
    slug_field = 'uuid'

# class @ListView(ListView):
#     model = @
#     template_name = "web/@_list.html"


@login_required(login_url="/mds/web/login/")
def portal(request):
    from mds.core import models as objects
    metadata = _metadata(request)
    context = {
        'flavor': metadata.flavor,
        'errors': metadata.errors,
        'messages' : metadata.messages,
        'models' : objects.__all__
    }
    
    context['portal'] = portal_site
    return TemplateResponse(request,
        'web/index.html',
        context,
    )
