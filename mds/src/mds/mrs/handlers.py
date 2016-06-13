'''
Created on Aug 10, 2012

:author: Sana Development Team
:version: 2.0
'''
try:
    import json as simplejson
except ImportError, e:
    import simplejson
import sys, traceback
import logging

from django.conf import settings
from django.forms import ValidationError
from piston.handler import BaseHandler

from mds.core.handlers import EventHandler as BaseRequestHandler

from mds.api import LOGGER
from mds.api.contrib import openmrslib
from mds.api.responses import succeed, fail
from mds.api.decorators import logged
from mds.api.signals import EventSignal, EventSignalHandler
from mds.api.utils import printstack

from mds.api.v1.json import (render_json_response,
                              notification_submit, email_notification_submit, 
                              register_client_events,
                              binary_submit, binarychunk_submit, 
                              binarychunk_hack_submit, patient_get, 
                              patient_list, parseOne, parseAll )

from mds.api.v1.v2compatlib import spform_to_encounter, responses_to_observations      
from mds.api.v1.api import register_saved_procedure
from .forms import ProcedureSubmitForm
from .models import RequestLog

__all__ = ['AuthHandler', 
           'SavedProcedureHandler',
           'EventHandler',
           'RequestLogHandler',
           'NotificationHandler',
           'SMTPHandler',
           'BinaryHandler',
           'BinaryPacketHandler',
           'Base64PacketHandler',
           'PatientHandler']

@logged
class AuthHandler(BaseHandler):
    """ Handles status and authentication check requests. For working with
        openMRS versions 1.6+
    """
    allowed_methods = ('GET','POST')
    signals = { LOGGER:( EventSignal(), EventSignalHandler(RequestLog))}
    
    def read(self,request,*args, **kwargs):
        return self.create(request)
    
    def create(self,request, *args, **kwargs):
        """Validates user credentials with the backing data store.

         Request parameters:
            username
                a valid username
            password
                a valid password

         Parameters:
            request
                An authorization check request.
        """
        try:
            wsname = "sessions"
            auth = {"username": request.REQUEST.get("username", None),
                    "password" : request.REQUEST.get("password", None)}
            logging.info("username %s" % auth['username'])
            opener = openmrslib.build_opener(host=settings.OPENMRS_SERVER_URL)
            return succeed(opener.wsdispatch(wsname, auth=auth))
        except Exception, e:
            msg = "%s" % e
            logging.error(msg)
            return fail(msg)
    
@logged   
class SavedProcedureHandler(BaseHandler):
    """ Handles encounter requests. """
    allowed_methods = ('POST',)
    signals = { LOGGER:( EventSignal(), EventSignalHandler(RequestLog))}
    
    def create(self,request, *args, **kwargs):
        logging.info("Received saved procedure submission.")
        response = ''
        form = ProcedureSubmitForm(self.flatten_dict(request.POST))
        logging.debug("Data: %s" % form.data)
        try:
            form.full_clean()
            if not form.is_valid():
                raise ValidationError(form.errors)
            encounter, data, created = spform_to_encounter(form.cleaned_data)
            savedproc_guid  = form.cleaned_data['savedproc_guid']
            procedure_guid = form.cleaned_data['procedure_guid']
            responses = form.cleaned_data['responses']
            phone = form.cleaned_data['phone']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            result, message = register_saved_procedure(savedproc_guid,
                                                       procedure_guid,
                                                       responses,
                                                       phone,
                                                       username,
                                                       password)
            
            
            encounter.save()
            logging.debug("Saved encounter: " + encounter.uuid)
	    observations = responses_to_observations(encounter, data,sort=True)
	    
	    for obs in observations:
	        obs.save()
	        
	        if obs.is_complex:
	            obs.create_file()
	        
	    #result, message = True, encounter
            
            if result:
                response = succeed("Successfully saved the procedure: %s" % message)
                logging.info("Saved procedure successfully registered.")
            else:
                response = fail(message)
                logging.error("Failed to register procedure: %s" % message)
        except ValidationError, e:
            #for k,v in form._get_errors().items():
            #    logging.error("SavedProcedure argument %s:%s" % (k,v))
            for err in form.errors:
                logging.error('Field error...%s' % err)
            response = fail("Invalid ProcedureSubmitForm data")
            #raise Exception('Saved procedure submission was invalid')
    
        except Exception, e:
            et, val, tb = sys.exc_info()
            trace = traceback.format_tb(tb)
            error = "Exception : %s %s %s" % (et, val, trace[0])
            for tbm in trace:
                logging.error(tbm)
            response = fail(error)
        return response

class EventHandler(BaseRequestHandler):
    
    def create(self,request, *args, **kwargs):
        """Accepts a request for submitting client events.
        
        Request Parameters:
            client_id 
                The client phone number
            events 
                The client events
            
        Events should be submitted as a list in JSON formatted text with each 
        event having the following key/value pairs:
        
        Event
            event_type
                An event type
            event_value 
                An event value
            event_time 
                The time of the event in milliseconds since epoch
            encounter_reference 
                The encounter, or saved procedure, id
            patient_reference
                The patient id
            user_reference 
                TODO
        
        Parameters:
            request
                The client event log request.
        """
    
        client_id = request.REQUEST.get('client_id', None)
        events_json = request.REQUEST.get('events', None)
    
        if events_json is None or client_id is None:
            return render_json_response(fail("Could not parse eventlog submission."))
    
        logging.info("Received events parameter: %s" % events_json)
    
        try:
            events = simplejson.loads(events_json)
            result, message = register_client_events(client_id, events)
    
            response = None
            if result:
                response = succeed(message)
            else:
                response = fail(message)
        except Exception, e:
            logging.error("Error while processing events: %s" % e)
            response = fail("Could not parse eventlog submission.")
        return render_json_response(response)

class RequestLogHandler(BaseRequestHandler):
    """ Handles network request log requests. """
    allowed_methods = ('GET', 'POST')
    model = RequestLog
    
@logged    
class NotificationHandler(BaseHandler):
    """ Handles encounter requests. """
    allowed_methods = ('POST',)
    signals = { LOGGER:( EventSignal(), EventSignalHandler(RequestLog))}
    
    def create(self,request, *args, **kwargs):
        return notification_submit(request) 
@logged    
class SMTPHandler(BaseHandler):
    """ Handles encounter requests. """
    allowed_methods = ('POST',)
    signals = { LOGGER:( EventSignal(), EventSignalHandler(RequestLog))}
    
    def create(self,request, *args, **kwargs):
        return email_notification_submit(request)  

@logged
class BinaryHandler(BaseHandler):
    allowed_methods = ('POST',)
    signals = { LOGGER:( EventSignal(), EventSignalHandler(RequestLog))}
    
    def create(self,request, *args, **kwargs):
        return binary_submit(request)
    
@logged
class BinaryPacketHandler(BaseHandler):
    allowed_methods = ('POST',)
    signals = { LOGGER:( EventSignal(), EventSignalHandler(RequestLog))}
    
    def create(self,request, *args, **kwargs):
        return binarychunk_submit(request)
    
@logged
class Base64PacketHandler(BaseHandler):
    allowed_methods = ('POST',)
    signals = { LOGGER:( EventSignal(), EventSignalHandler(RequestLog))}
    
    def create(self,request, *args, **kwargs):
        return binarychunk_hack_submit(request)
    

@logged
class PatientHandler(BaseHandler):
    """ Handles patient requests. """
    allowed_methods = ('GET',)
    signals = { LOGGER:( EventSignal(), EventSignalHandler(RequestLog))}
    
    def read(self,request, id=None, **kwargs):
        """ Returns zero or more patients from OpenMRS
        """
        try:
            opener = openmrslib.build_opener(host=settings.OPENMRS_SERVER_URL)
            query = self.flatten_dict(request.GET)
            username = query.pop("username")
            password = query.pop("password")
            if id and id != 'list':
                response = opener.getPatient(username, password, id)   
                if openmrslib.OPENMRS_VERSION < 1.8:
                    message = parseOne(response)
                else:
                    message =response
                if len(message) == 0:
                    return fail("")
            else:
                response = opener.getAllPatients(username, password, query=query)   
                if openmrslib.OPENMRS_VERSION < 1.8:
                    message = parseAll(response)
                else:
                    message = ""
                    logging.debug("Response: %s" % response) 
                    for p in response:
                        logging.debug(p)
                        firstname = p["givenName"]
                        lastname = p["family_name"]
                        gender = p["gender"]
                        birthdate = p["birthdate"]
                        uuid = p["uuid"]
                        patient = "%s%s%s%s%s%s".format(firstname.lower(),
                                                        birthdate[0:4],
                                                        birthdate[5:7],
                                                        birthdate[8:10],
                                                        lastname.lower(),
                                                        gender.lower())
                        message.append(patient)
            logging.debug("message: %s" % message)
            return succeed(message)
        except Exception, e:
            logging.error("Error: %s" % str(e))
            printstack(e)
            return fail("%s" % e)
        
        
    