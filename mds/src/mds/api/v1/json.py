"""Http request handlers for JSON encoded submissions. 

Logging
-------
Although not documented The following methods use the *enable_logging* decorator
to trace the log events per request: ::

    binarychunk_submit
    binarychunk_hack_submit
    email_notification_submit
    eventlog_submit
    notification_submit
    patient_get
    patient_list
    procedure_submit
    savedprocedure_get
    savedprocedure_list
    syc_encounter

:Authors: Sana Dev Team
:Version: 1.1
"""

try:
    import json as simplejson
except ImportError, e:
    import simplejson
import sys, traceback
import logging
import cjson
import urllib2
import telnetlib
import urllib
from xml.dom import minidom

from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import render_to_response

from ..responses import render_json_response, succeed, fail

from mds.mrs.forms import *
from mds.api.contrib.openmrslib import openmrs16 as openmrs
from mds.api.contrib.smslib.messages import send_notification

from mds.api.v1.api import register_saved_procedure
from mds.api.v1.api import register_binary
from mds.api.v1.api import register_binary_chunk
from mds.api.v1.api import register_client_events

from mds.mrs.forms import *
from mds.mrs.models import Notification, SavedProcedure


MSG_MDS_ERROR = 'Dispatch Error'

def validate_credentials(request):
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
        username = request.REQUEST.get("username", None)
        password = request.REQUEST.get("password", None)
        logging.info("username: " + username)

        response = ''
        omrs = openmrs.OpenMRS(username,password,
                          settings.OPENMRS_SERVER_URL)
        if omrs.validate_credentials(username, password):
            response = succeed("username and password validated!")
        else:
            response = fail("username and password combination incorrect!")
    except Exception, e:
        msg = '%s validate_credentials' % MSG_MDS_ERROR
        logging.error('%s %s' % (msg,str(e)))
        response = fail(msg)
    return render_json_response(response)

def procedure_submit(request):
    """Accepts a request to send collected encounter data to the data store.
    See ProcedureSubmitForm for request parameters
    
    Parameters:
        request
            The data uploaded from the client.
    """
    try:
        logging.info("Received saved procedure submission.")
        form = ProcedureSubmitForm(request.POST)
        response = ''
        if form.is_valid():
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

            if result:
                response = succeed("Successfully saved the procedure: %s" % message)
                logging.info("Saved procedure successfully registered.")
            else:
                response = fail(message)
                logging.error("Failed to register procedure: %s" % message)
        else:
            logging.error("Saved procedure submission was invalid, dumping REQUEST.")
            for k,v in request.REQUEST.items():
                logging.error("SavedProcedure argument %s:%s" % (k,v))
            response = fail("Could not parse submission : missing parts or invalid data?")

    except Exception, e:
        et, val, tb = sys.exc_info()
        trace = traceback.format_tb(tb)
        error = "Exception : %s %s %s" % (et, val, trace[0])
        for tbm in trace:
            logging.error(tbm)
        response = fail(error)
    return render_json_response(response)

def binarychunk_submit(request):
    """Accepts requests which contain a packetized chunk of binary data 
    uploaded for an encounter whose text has already been submitted but is 
    waiting for all binary from the mobile client to be received prior to 
    uploading to the data store. 
        
    Note: There is a naming inconsistency between this function's use of 
    procedure_guid and that of the register_saved_procedure function.

    Request parameters, per BinaryChunkSubmitForm.
    
    Parameters:
        request
            A binary chunk sent from a client.
    """    
    response = ''
    form = BinaryPacketForm(request.POST, request.FILES)

    if form.is_valid():
        logging.info("Received valid binarychunk form")

        procedure_guid = form.cleaned_data['procedure_guid']
        element_id = form.cleaned_data['element_id']
        element_type = form.cleaned_data['element_type']
        binary_guid = form.cleaned_data['binary_guid']
        file_size = form.cleaned_data['file_size']
        byte_start = form.cleaned_data['byte_start']
        byte_end = form.cleaned_data['byte_end']
        byte_data = form.cleaned_data['byte_data']
        logging.info("File _size: %s" % file_size )

        try:
            result, message = register_binary_chunk(procedure_guid,
                                                    element_id,
                                                    element_type,
                                                    binary_guid,
                                                    file_size,
                                                    byte_start,
                                                    byte_end,
                                                    byte_data.chunks())
            if result:
                response = succeed("Successfully saved binary chunk: %s" 
                                        % message)
            else:
                response = fail("Failed to save the binary chunk: %s" 
                                     % message)
        except Exception, e:
            et, val, tb = sys.exc_info()
            trace = traceback.format_tb(tb)
            error = "Exception : %s %s %s" % (et, val, trace[0])
            for tbm in trace:
                logging.error(tbm)
            response = fail(error)
        logging.info("Finished processing binarychunk form")
    else:
        logging.error("Received invalid binarychunk form")
        for k,v in request.REQUEST.items():
            if k == 'byte_data':
                logging.debug("%s:(binary length %d)" % (k,len(v)))
            else:
                logging.debug("%s:%s" % (k,v))
        response = fail("Invalid form: %s" % form.errors)
    return render_json_response(response)

def binarychunk_hack_submit(request):
    """Accepts requests which contain a packetized chunk of binary data 
    encoded as base64 text for an encounter whose text has already been 
    submitted but waiting for all binary data from the mobile client to be 
    received prior to uploading to the data store
        
    Note: There is a naming inconsistency between this function's use of 
    procedure_guid and that of the register_saved_procedure function.
    
    Parameters
        request
            A client request.
    """    
    response = ''
    form = Base64PacketForm(request.POST, request.FILES)

    if form.is_valid():
        logging.info("Received valid binarychunk-hack form")

        procedure_guid = form.cleaned_data['procedure_guid']
        element_id = form.cleaned_data['element_id']
        element_type = form.cleaned_data['element_type']
        binary_guid = form.cleaned_data['binary_guid']
        file_size = form.cleaned_data['file_size']
        byte_start = form.cleaned_data['byte_start']
        byte_end = form.cleaned_data['byte_end']
        byte_data = form.cleaned_data['byte_data']

        # This hack submits byte_data as base64 encoded, so decode it.
        byte_data = byte_data.decode('base64')

        try:
            result, message = register_binary_chunk(procedure_guid,
                                                    element_id,
                                                    element_type,
                                                    binary_guid,
                                                    file_size,
                                                    byte_start,
                                                    byte_end,
                                                    [byte_data,])
            if result:
                response = succeed("Successfully saved the binary chunk: %s" % message)
            else:
                response = fail("Failed to save the binary chunk: %s" % message)
        except Exception, e:
            logging.error("registering binary chunk failed: %s" % e)
            response = fail("Registering binary chunk failed: %s" % e)
        logging.info("Finished processing binarychunk form")
    else:
        logging.error("Received invalid binarychunk form")
        for k,v in request.REQUEST.items():
            if k == 'byte_data':
                logging.debug("%s:(binary length %d)" % (k,len(v)))
            else:
                logging.debug("%s:%s" % (k,v))
        response = fail("Invalid form: %s" % form.errors)

    logging.info("Sending response %s" % response)
    return render_json_response(response)

def binary_submit(request):
    """Accepts requests which contain a non-packetized binary uploaded for an 
    encounter whose text has already been submitted but waiting for all 
    binary data from the mobile client. 
    
    See BinarySubmitForm for request parameters.
        
    Note: There is a naming inconsistency between this function's use of 
    procedure_guid and that of the register_saved_procedure function.
    
    Parameters:
        request
            A binary POST submission.
    """    
    response = ''

    form = BinarySubmitForm(request.REQUEST)
    data = request.FILES.get('data',None)

    if form.is_valid() and data:
        logging.info("Received a valid Binary submission form")
        element_id = form.cleaned_data['element_id']
        procedure_guid = form.cleaned_data['procedure_guid']

        register_binary(procedure_guid, element_id, data)

        response = succeed("Successfully saved the binary")
        logging.info("Done processing Binary submission form")
    else:
        logging.info("Received an invalid Binary submission form")
        response = fail("Could not parse submission. Missing parts?")

    return render_json_response(response)

class OpenMRSQueryForm(forms.Form):
    """A generic OpenMRS form with authorization information.
    
    :Authors: Sana dev team
    :Version: 1.1
    """
    username = forms.CharField(required=True, max_length=256)
    password = forms.CharField(required=True, max_length=256)

def patient_list(request):
    """Accepts a request to return a list of all patients from the backing data
    store. Used for synching the mobile client.
    
    Warning: This can return a significant amount of patient data.
    
    Request parameters:
        username
            a valid username
        password
            a valid password
            
    Parameters:
        request
            A HTTP request for a patient list.
    
    :Authors: Sana dev team
    :Version: 1.1
    """
    logging.info("entering patient list proc")
    username = request.REQUEST.get("username", None)
    password = request.REQUEST.get("password", None)
    url = settings.OPENMRS_SERVER_URL
    try:
        list = getAllPatients(url, username, password)
        data = parseAll(list)
        logging.info("we finished getting the patient list")
        response = succeed(data)
    except Exception, e:
        et, val, tb = sys.exc_info()
        trace = traceback.format_tb(tb)
        error = "Exception : %s %s %s" % (et, val, trace[0])
        for tbm in trace:
            logging.error(tbm)
        logging.error("Got exception while fetching patient list: %s" % e)
        response = fail("Problem while getting patient list: %s" % e)
    return render_json_response(response)

def patient_get(request, id):
    """Accepts a request to validate a patient id from the backing data store. 
    Successful retrieval will return a a SUCCESS message with the patient data 
    formatted as::
        
        <given_name><yyyy><mm><dd><family_name>f
    
    Request params:
        username
            a valid username
        password
            a valid password
            
    Parameters:
        request
            A patient request by id.
        id
            The id to look up.
    """
    logging.info("entering patient get proc")
    username = request.REQUEST.get("username", None)
    password = request.REQUEST.get("password", None)
    url = settings.OPENMRS_SERVER_URL
    logging.info("About to getPatient")
    try:
        patient = getPatient(url, username, password, id)
        data = parseOne(patient)
        response = succeed(data)
    except Exception, e:
        et, val, tb = sys.exc_info()
        trace = traceback.format_tb(tb)
        error = "Exception : %s %s %s" % (et, val, trace[0])
        for tbm in trace:
            logging.error(tbm)
        response = fail("couldn't get patient %s" % error)
    logging.info("finished patient_get")
    return render_json_response(response)

def parseAll(s):
    """Parses multiple patients from xml text.
    
    Note: This function is OpenMRS specific
    
    Parameters:
        s
            xml text string containing patient data
    """
    patients = ""
    doc = minidom.parseString(s)
    doc = doc.childNodes[0]
    if (len(doc.childNodes)==0):
        return ""
    for i in range(0,len(doc.childNodes)):
        node = doc.childNodes[i]
        gender = node.getAttribute("gender")
        birthdate = node.getAttribute("birthdate")
        namenode = node.getElementsByTagName("name")[0]
        firstname = namenode.getElementsByTagName("givenName")[0].firstChild.data.strip()
        lastname = namenode.getElementsByTagName("familyName")[0].firstChild.data.strip()
        ids = node.getElementsByTagName("identifierList")[0].getElementsByTagName("identifier")
        for j in range(0,len(ids)):
            #format the string and add it to the list. birthdates are year+month+day
            #format is jenny19880926liu10909f where 10909=id number
            patient = firstname.lower() + birthdate[0:4] + birthdate[5:7] + birthdate[8:10] + lastname.lower() + ids[j].firstChild.data + gender.lower() + "##"
            patients += patient
    return patients

def parseOne(s):
    """Parses a single patient from xml text.
    
    Note: THis function is OpenMRS specific
        
    Parameters:
        s
            xml text string containing patient data
    """
    doc = minidom.parseString(s)
    doc = doc.childNodes[0]
    if (len(doc.childNodes)==0):
        print "patient data empty, no such user"
        return ""
    node = doc.childNodes[0]
    gender = node.getAttribute("gender")
    birthdate = node.getAttribute("birthdate")
    namenode = node.getElementsByTagName("name")[0]
    firstname = namenode.getElementsByTagName("givenName")[0].firstChild.data.strip()
    lastname = namenode.getElementsByTagName("familyName")[0].firstChild.data.strip()
    #format the string and add it to the list. birthdates are year+month+day
    #format is jenny19880926liuf
    patient = firstname.lower() + birthdate[0:4] + birthdate[5:7] + birthdate[8:10] + lastname.lower() + gender.lower()
    return patient

def getAllPatients(uri, user, passwd):
    """Gets all patients from OpenMRS.
    
    Parameters:
        uri
            The server url.
        user
            A valid username.
        passwd
            A valid password.
    """
    logging.debug("getAllPatients")
    omrs = openmrs.OpenMRS(user, passwd, settings.OPENMRS_SERVER_URL)
    if omrs.validate_credentials(user, passwd):
        result = omrs.getAllPatients(user, passwd)
        return result
    else:
        return None

def getPatient(uri, user, passwd, userid):
    """Executes get request to the data store for checking a patient id.
    
    Parameters:
        uri
            The server url.
        user
            A valid username.
        passwd
            A valid password.
    """
    # Create an OpenerDirector with support for Basic HTTP Authentication...
    omrs = openmrs.OpenMRS(user, passwd, settings.OPENMRS_SERVER_URL)
    if omrs.validate_credentials(user, passwd):
        result = omrs.getPatient(user, passwd, userid)
        return result
    else:
        return None

def notification_submit(request):
    """Handles notification submissions
        
    Request params
        phoneIdentifier
            The phone number
        notificationText
            The notification 
        patientIdentifier
            A patient Identifier
    
    Parameters:
        request
            Incoming http request
    """
    phoneId = request.REQUEST.get("phoneIdentifier", None)
    text = request.REQUEST.get("notificationText", None)
    caseIdentifier = request.REQUEST.get("caseIdentifier", None)
    patientIdentifier = request.REQUEST.get("patientIdentifier", None)
    delivered = False

    logging.info("Notification submit received")

    for key,value in request.REQUEST.items():
        logging.info("Notification submit %s:%s" % (key,value))

    response = fail('Failed to register notification.')
    if phoneId and text and caseIdentifier and patientIdentifier:
        n = Notification(client=phoneId,
                         patient_id=patientIdentifier,
                         message=text,
                         procedure_id=caseIdentifier,
                         delivered=delivered)
        n.save()
        try:
            delivered = send_notification(n, phoneId)
            response = succeed('Successfully sent notification.')
        except Exception, e:
            logging.error("Got error while trying to send notification: %s" % e)
            response = succeed('Failed to send notification. Error')
            
    return render_json_response(response)

def email_notification_submit(request):
    """Accepts and sends a request to forward an email notification.
    
    Request Params:
        emailAddreses
            One or more recipient email addresses
        caseIdentifier
            The encounter, or saved procedure, id
        patientIdentifier
            The patient id
        subject
            the subject line of the email
        notificationText
            the message body
            
    Parameters:
        request
            Incoming http request
    """
    addresses = request.REQUEST.get("emailAddresses",None)
    caseIdentifier = request.REQUEST.get("caseIdentifier", None)
    patientId = request.REQUEST.get("patientIdentifier", None)
    subject = request.REQUEST.get("subject", "")
    message = request.REQUEST.get("notificationText", "")

    logging.info("Email notification submit received")

    for key,value in request.REQUEST.items():
        logging.info("Notification submit %s:%s" % (key,value))

    response = fail('Failed to register email notification.')

    try:
        emailAddresses = cjson.decode(addresses)
    except Exception, e:
        response = fail('Got error when trying to parse email addresses.')

    if addresses and caseIdentifier and patientId:
        try:
            send_mail(subject, message, settings.OPENMRS_REPLYTO,
                          emailAddresses, fail_silently=False)
            response = succeed('Successfully registered email notification')
        except Exception, e:
            logging.error('Email could not be sent: %s' % e)
    return render_json_response(response)


def eventlog_submit(request):
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

def parseSavedProcedureAll(s):
    """ Parses zero or more encounters from the backing store. This is currently
    bound to OpenMRS.
    
    Parameters    
        s
            XML text containing the encounters.
    """
    patients = ""
    doc = minidom.parseString(s)
    doc = doc.childNodes[0]
    for i in range(0,len(doc.childNodes)):
        node = doc.childNodes[i]
        gender = node.getAttribute("gender")
        birthdate = node.getAttribute("birthdate")
        namenode = node.getElementsByTagName("name")[0]
        firstname = namenode.getElementsByTagName("givenName")[0].firstChild.data.strip()
        lastname = namenode.getElementsByTagName("familyName")[0].firstChild.data.strip()
        ids = node.getElementsByTagName("identifierList")[0].getElementsByTagName("identifier")
        for j in range(0,len(ids)):
            #format the string and add it to the list. birthdates are year+month+day
            #format is jenny19880926liu10909f where 10909=id number
            patient = firstname.lower() + birthdate[0:4] + birthdate[5:7] + birthdate[8:10] + lastname.lower() + ids[j].firstChild.data + gender.lower() + "##"
            patients += patient
    return patients
        

def saved_procedure_get(request, id):
    """Accepts a request for an encounter by its id. 
    
    Parameters:
        request
            The client HTTP request.
        id
            the saved procedure id.
    """
    logging.info("entering saved_procedure")
    username = request.REQUEST.get("username", None)
    password = request.REQUEST.get("password", None)
    url = settings.OPENMRS_SERVER_URL
    logging.info("About to getPatient")
    try:
        #patient = getPatient(url, username, password, id)
        #data = parseOne(patient)
        
        saved_procedure = SavedProcedure.objects.get(guid=id)
        
        response = succeed([saved_procedure.procedure_guid, 
                            saved_procedure.encounter, 
                            saved_procedure.responses])
    except Exception, e:
        logging.error("Got error %s" % e)
        response = fail("couldn't find encounter")
    logging.info("finished returning saved_procedure %s : %s : %s" 
                 % (saved_procedure.procedure_guid, saved_procedure.encounter, 
                    saved_procedure.responses))
    return render_json_response(response)


def saved_procedure_list(request):
    """For synching saved procedures with mobile clients.
    
    Request Params
        username
            A valid username.
        password
            A valid password.
    
    Parameters:
        request
            A client request to synch
    """
    logging.info("entering patient list proc")
    username = request.REQUEST.get("username", None)
    password = request.REQUEST.get("password", None)
    url = settings.OPENMRS_SERVER_URL
    try:
        saved_procedures = SavedProcedure.objects.get(encounter=id)
        data = parseSavedProcedureAll(saved_procedures)
        logging.info("we finished getting the patient list")
        response = succeed(data)
    except Exception, e:
        logging.error("Got exception while fetching patient list: %s" % e)
        response = fail("Problem while getting patient list: %s" % e)
    return render_json_response(response)


def syc_encounters(request, patient_id, encounters=None):
    """For synching specific saved procedures for a patient with mobile clients.
    
    Request Params
        username
            A valid username.
        password
            A valid password.
    
    Parameters:
        request
            A client request to synch
        patient_id
            The patient to look up
        encounters
            A list of encounters to look up.
        
    """
    logging.info("Syncing encounters from MDS to client with patientID: %s" % patient_id)
    logging.info("Excluding following encounters: %s" % encounters)

    if not encounters == None:
        enc = encounters.split(':')
        encounters = SavedProcedure.objects.filter(responses__icontains='"patientId":{"answer":"%s"' % patient_id).exclude(encounter= -1).exclude(encounter__in=enc)
    else:
        encounters = SavedProcedure.objects.filter(responses__icontains='"patientId":{"answer":"%s"' % patient_id).exclude(encounter= -1)

    logging.info('Encounters found : %s' % encounters.count())
    cleaned_encounters = {}
      
    procedure_guids = ''
    
    for encounter in encounters:
        answerMap = ''
        response = {}
        responses = cjson.decode(encounter.responses,True)
        
        for eid, attr in responses.items():
            response[eid] = attr.get('answer')
        answerMap = cjson.encode(response)
        cleaned_encounters[encounter.encounter] = response
        procedure_guids += ('%s#' % encounter.procedure_guid)
    
    data = cjson.encode(cleaned_encounters)
    logging.info(data)
    logging.info(procedure_guids)
    logging.info("Returning encounters")
    response = succeed(procedure_guids, data)
    
    logging.info("finished sync_encounters")
    return render_json_response(response)



