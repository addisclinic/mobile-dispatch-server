'''


'''
import copy

from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse, NoReverseMatch
from django.template.response import TemplateResponse
from django.utils import six
from django.utils.text import capfirst
from django.utils.translation import ugettext as _
from django.views import generic

from django.conf import settings

def build_urls(model_list):
    pass
    
class Portal(object):

    _urlcache = None

    @property
    def urls(self):
        pass
        
    def register_model(self,model, view=None, app=None,**kwargs):
        pass
        
    def register_manager(self, model, view=None, app=None, **kwargs):
        pass
    
    def register_report(self, report, **kwargs):
        pass
    
    def register_form(self,form,**kwargs):
        pass
        
    def register_task(self,model,**kwargs):
        pass

class PortalView(object):

    exclude = ()
    fields = ()
    form = None
    opts = {}
    _name = None
    _model = None
    
    def __init__(self, name, **options):
        super(PortalSite,self)
        self._model = model
        self._name = name
        opts = copy.deepcopy(options)
    
    @property
    def name(self):
        return self._name



def PortalModelView(PortalView):
    

    def __init__(self, model, form=None, **opts):
        super(PortalModelView, self)

    @property
    def url(self):
        pass
        
    def edit_view(self, slug):
        pass
        
    def create_view(self, slug):
        pass
        
    def update_view(self, slug):
        pass
        
    def list_view(self, slug):
        pass
    
def PortalReportView(PortalView):
    pass

class PortalSite(object):
    name = None
    _registry = {}
    opts = {}
    
    class NavItem(object):
        label = None
        url = None
        children = []
        
        def __init__(self, label, url):
            super(NavItem, url) 
    
    def __init__(self, name='portal',  **kwargs):
        super(PortalSite,self)
        self.name = name
        opts = copy.deepcopy(kwargs)
        
    @property
    def sidebar(self):
        ''' Return a list of menu items to include in a sidebar menu.
        '''
        pass


    def index(self, request, extra_context=None):
        pass

    def register(self, model_or_iterable, portal_class=None, **options):
        pass

    def get_urls(self):
        from django.conf.urls import patterns, url, include

        #if settings.DEBUG:
        #    self.check_dependencies()

        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.admin_view(view, cacheable)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        # Admin-site-wide views.
        urlpatterns = patterns('',
            url(r'^$',
                wrap(self.index),
                name='index'),
            url(r'^logout/$',
                wrap(self.logout),
                name='logout'),
        )

        # Add in each model's views.
        for model, model_admin in six.iteritems(self._registry):
            urlpatterns += patterns('',
                url(r'^%s/%s/' % (model._meta.app_label, model._meta.model_name),
                    include(model_admin.urls))
            )
        return urlpatterns

    @property
    def urls(self):
        return self.get_urls(), self.app_name, self.name
        
    @property
    def login(self):
        pass
        
    @property
    def logout(self):
        pass
        
        
    def register(self, portal_view,  **options):
        pass
        

site = {
        'name' : 'MDS2 Web Portal',
        'app' : 'web',
        'sites' : [
           {
                'label':'Users',
                'views': [
                    { 
                        'label': 'View all users',
                        'context_name':'user-list',
                    },
                    { 
                        'label': 'New User',
                        'context_name':'user-create',
                    },
                    { 
                        'label': 'View all CHWs',
                        'context_name':'observer-list',
                    },
                    { 
                        'label': 'New CHW',
                        'context_name':'observer-create',
                    }
                ]
            },

            {
                'label':'Data',
                'views': [
                    { 
                        'label': 'concepts',
                        'context_name':'concept-list',
                    },
                    { 
                        'label': 'devices',
                        'context_name':'device-list',
                    },
                    { 
                        'label': 'encounters',
                        'context_name':'encounter-list',
                    },
                    { 
                        'label': 'locations',
                        'context_name':'location-list',
                    },
                    { 
                        'label': 'observations',
                        'context_name':'observation-list',
                    },
                    { 
                        'label': 'patients',
                        'context_name':'subject-list',
                    },
                    { 
                        'label': 'procedures',
                        'context_name':'procedure-list',
                    },
                ]
            },

            {
                'label':'Tasks',
                'views': [
                    { 
                        'label': 'Assigned Tasks',
                        'context_name':'encountertask-list',
                    },
                    { 
                        'label': 'New',
                        'context_name':'encountertask-create',
                    }
                ]
            },
            {
                'label':'Reports',
                'views':[]
            },
        ]
    }

_portal = None

def detailview_factory(model, form_class=None, fields=None):
    pass
    
def createview_factory(model, form_class=None, fields=None):
    pass
    
def listview_factory(model, form_class=None, fields=None):
    pass

def updateview_factory(model, form_class=None, fields=None):
    pass

def get_or_create_portal(portal_site=None):
    if not _portal:
        _portal = portal_site if portal_site else PortalSite()

    _portal.register(portal_view, **options)

