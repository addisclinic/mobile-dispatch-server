''' The OpenMRS request handlers and utilities'''

from django.conf import settings

from .openmrs16 import OpenMRS as OpenMRS16
from .openmrs19 import OpenMRS as OpenMRS19
from .handlers import OpenMRSHandler

__all__ = ['version',
           'host',
           'OPENMRS_VERSION',
           'OPENMRS_HOST',
           'build_opener'
           'get_handler',
    ]

def version():
    return settings.OPENMRS_VERSION

def host():
    return settings.OPENMRS_SERVER_URL

OPENMRS_VERSION=version()
""" Default supported version for the API."""

OPENMRS_HOST = host()
""" Default OpenMRS url"""
        
def build_opener(host=OPENMRS_HOST, version=OPENMRS_VERSION):
    if version < 1.8:
        return OpenMRS16(host)
    else:
        return OpenMRS19(host)
    
def get_handler(model, host=OPENMRS_HOST):
    return OpenMRSHandler(host)
