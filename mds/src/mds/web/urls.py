"""The Django url to handler mappings.


:Authors: Sana dev team
:Version: 2.0
"""
from django.conf.urls import patterns, url, include
from django.contrib.auth import views as auth_views

from .views import *

urlpatterns = patterns(    
    #'mds.web',
    '',
    url(r'^$',
        'mds.web.views.portal',
        name="portal"),
    url(r'^accounts/login/$', auth_views.login),
    url(r'^login/$', 'mds.web.views.login', name='login'),
    url(r'^logout/$', 'mds.web.views.logout',name='logout'),
    #url(r'^login/$', 'django.contrib.auth.views.login'),
    #url(r'^mobile/authenticate/$', 'views.mobile_authenticate', name='mobile-authenticate'),
    #url(r'^etask/$', 'mds.web.views.encounter_task', name='encounter-task'),
    #url(r'^etask/list/$', 'mds.web.views.task_list', name='encounter-task-list'),
    #url(r'^etask/(?P<uuid>[^/]+)/$', 'mds.web.views.edit_encounter_task', name='edit-encounter-task'),
    #url(r'^registration/$', 'mds.web.views.registration', name='register-patient'),
    #url(r'^intake/$', 'mds.web.views.web_encounter', name='intake'),

    url(r'^logs/$', 'mds.web.views.logs', name='log-index'),
    url(r'^logs/list/$', 'mds.web.views.log_list', name='log-list'),


    # Replace @ with name of Model class
    #url(r'^@/$', @ListView.as_view(), name='@-list'),
    #url(r'^@/new/$', @CreateView.as_view(), name='@-new'),
    #url(r'^@/(?P<uuid>[^/]+)/$', @UpdateView.as_view(), name='@-edit'),

    #url(r'^subject/$', 'mds.web.views.subject', name='subject'),
    #url(r'^concept/$', 'mds.web.views.concept', name='')
    
    # User objects
    url(r'^user/$', UserListView.as_view(), name='user-list'),
    url(r'^user/new/$', UserCreateView.as_view(), name='user-create'),
    url(r'^user/(?P<pk>[^/]+)/$', UserUpdateView.as_view(), name='user-edit'),
    url(r'^user/(?P<pk>\d+)/detail/$', UserDetailView.as_view(), name='user-detail'),
    
    # Concepts
    url(r'^concept/$', ConceptListView.as_view(), name='concept-list'),
    url(r'^concept/new/$', ConceptCreateView.as_view(), name='concept-create'),
    url(r'^concept/(?P<pk>[^/]+)/$', ConceptUpdateView.as_view(), name='concept-edit'),
    url(r'^concept/(?P<pk>\d+)/detail/$', ConceptDetailView.as_view(), name='concept-detail'),
    
    # Devices
    url(r'^device/$', DeviceListView.as_view(), name='device-list'),
    url(r'^device/new/$', DeviceCreateView.as_view(), name='device-create'),
    url(r'^device/(?P<pk>[^/]+)/$', DeviceUpdateView.as_view(), name='device-edit'),
    url(r'^device/(?P<pk>\d+)/detail/$', DeviceDetailView.as_view(), name='device-detail'),

    # Encounters
    url(r'^encounter/$', EncounterListView.as_view(),name='encounter-list'),
    url(r'^encounter/new/$', EncounterCreateView.as_view(), name='encounter-create'),
    url(r'^encounter/(?P<pk>\d+)/$', EncounterUpdateView.as_view(), name='encounter-edit'),
    url(r'^encounter/(?P<pk>\d+)/detail/$', EncounterDetailView.as_view(), name='encounter-detail'),

    # Locations
    url(r'^location/$', LocationListView.as_view(), name='location-list'),
    url(r'^location/new/$', LocationCreateView.as_view(), name='location-create'),
    url(r'^location/(?P<pk>[^/]+)/$', LocationUpdateView.as_view(), name='location-edit'),
    url(r'^location/(?P<pk>[^/]+)/detail/$', LocationDetailView.as_view(), name='location-detail'),

    # Observations
    url(r'^observation/$', ObservationListView.as_view(), name='observation-list'),
    url(r'^observation/new/$', ObservationCreateView.as_view(), name='observation-create'),
    url(r'^observation/(?P<pk>[^/]+)/$', ObservationUpdateView.as_view(), name='observation-edit'),
    url(r'^observation/(?P<pk>\d+)/detail/$', ObservationDetailView.as_view(), name='observation-detail'),
    
    # Observers
    url(r'^observer/$', ObserverListView.as_view(), name='observer-list'),
    url(r'^observer/new/$', ObserverCreateView.as_view(), name='observer-create'),
    url(r'^observer/(?P<pk>[^/]+)/$', ObserverUpdateView.as_view(), name='observer-edit'),
    url(r'^observer/(?P<pk>\d+)/detail/$', ObserverDetailView.as_view(), name='observer-detail'),
    
    # Procedures
    url(r'^procedure/$', ProcedureListView.as_view(),name='procedure-list'),
    url(r'^procedure/new/$', ProcedureCreateView.as_view(), name='procedure-create'),
    url(r'^procedure/(?P<pk>\d+)/$', ProcedureUpdateView.as_view(), name='procedure-edit'),
    url(r'^procedure/(?P<pk>\d+)/detail/$', ProcedureDetailView.as_view(), name='procedure-detail'),
    
    url(r'^subject/$', SubjectListView.as_view(),name='subject-list'),
    url(r'^subject/new/$', SubjectCreateView.as_view(),name='subject-create'),
    url(r'^subject/(?P<pk>[^/]+)/$', SubjectUpdateView.as_view(),name='subject-edit'),
    url(r'^subject/(?P<pk>\d+)/detail/$', SubjectDetailView.as_view(), name='subject-detail'),
    

    url(r'^encountertask/$', EncounterTaskListView.as_view(),name='encountertask-list'),
    url(r'^encountertask/new/$', EncounterTaskCreateView.as_view(),name='encountertask-create'),
    url(r'^encountertask/(?P<pk>[^/]+)/$', EncounterTaskUpdateView.as_view(),name='encountertask-edit'),
    url(r'^encountertask/(?P<pk>\d+)/detail/$', EncounterTaskDetailView.as_view(), name='encountertask-detail'),
)

