from django.conf import settings
from django.conf.urls import patterns, url, include
#from django.views.generic.simple import redirect_to

from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', 'clients.views.version', name="android"),
    )