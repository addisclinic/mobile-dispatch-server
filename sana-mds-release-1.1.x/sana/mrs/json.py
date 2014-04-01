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
from __future__ import absolute_import

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
from django.template import loader
from django.http import HttpResponse
from django import forms
from django.core.mail import send_mail
from django.shortcuts import render_to_response

from sana.mrs import openmrs
from sana.mrs.api import register_saved_procedure
from sana.mrs.api import register_binary
from sana.mrs.api import register_binary_chunk
from sana.mrs.api import register_client_events
from sana.mrs.util import enable_logging, mark
from sana.mrs.models import Notification, SavedProcedure

MSG_MDS_ERROR = 'Dispatch Error'

def render_json_template(*args, **kwargs):
    """Renders a JSON template, and then calls render_json_response(). 
    
    Parameters:
        args
            list of items to render 
        kwargs
            keyword/value pairs to render
    """
    data = loader.render_to_string(*args, **kwargs)
    return render_json_response(data)

def render_json_response(data):
    """Sends an HttpResponse with the X-JSON header and the right mimetype.
    
    Parameters:
        data
            message content
    """
    resp = HttpResponse(data, mimetype=("application/json; charset=" +
                                        settings.DEFAULT_CHARSET))
    resp['X-JSON'] = data
    return resp

def json_fail(message):
    """Creates a formatted failure response. Response format::
    
        {'status':'FAILURE', 'message': message }
    
    Parameters:
        message
            Response message body
    
    """
    response = {
        'status': 'FAILURE',
        'data': message,
        }
    return cjson.encode(response)

def json_succeed(data, encounter=None):
    """Creates a formatted success response. Response format:: 
    
        {'status':'SUCCESS', 'message': message }
    
    Parameters:
        message
            The response message body
    """
    response = {
        'status': 'SUCCESS',
        'data': data,
        }
    if encounter:
        response['encounter'] = encounter
    return cjson.encode(response)

def json_savedprocedure_succeed(savedproc_guid, encounter, data):
    """Creates a formatted success response for returning encounter data. 
    Response format:: 
    
        {'status':'SUCCESS', 
        'data': data,
        'encounter': encounter,
        'procedure_guid': procedure_guid, }
    
    Parameters:
        savedproc_guid
            an encounter, or saved procedure, id
        encounter
            encounter
        data
            encounter text data
    
    """
    response = {
        'status': 'SUCCESS',
        'data': data,
        'encounter': encounter,
        'procedure_guid': savedproc_guid,
        }
    return cjson.encode(response)

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
            response = json_succeed("username and password validated!")
        else:
            response = json_fail("username and password combination incorrect!")
    except Exception, e:
        msg = '%s validate_credentials' % MSG_MDS_ERROR
        logging.error('%s %s' % (msg,str(e)))
        response = json_fail(msg)
    return render_json_response(response)

class ProcedureSubmitForm(forms.Form):
    """Http POST form for encounter uploads.
    
    Request Parameters
    
    ============== =========================================
         Label                    Description
    ============== =========================================
    savedproc_guid the phone generated encounter id
    procedure_guid the procedure identifier, usually a title
    responses      the JSON encoded encounter data
    phone          the client id, usually phone number
    username       a valid username
    password       a valid password
    ============== =========================================
    
    :Authors: Sana dev team
    :Version: 1.1
    """
    username = forms.CharField(required=True, max_length=256)
    password = forms.CharField(required=True, max_length=256)
    savedproc_guid = forms.CharField(required=True, max_length=512)
    procedure_guid = forms.CharField(required=True, max_length=512)
    responses = forms.CharField(required=True)
    phone = forms.CharField(max_length=255, required=False, initial='')
    

@enable_logging
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
                response = json_succeed("Successfully saved the procedure: %s" % message)
                logging.info("Saved procedure successfully registered.")
            else:
                response = json_fail(message)
                logging.error("Failed to register procedure: %s" % message)
        else:
            logging.error("Saved procedure submission was invalid, dumping REQUEST.")
            for k,v in request.REQUEST.items():
                logging.error("SavedProcedure argument %s:%s" % (k,v))
            response = json_fail("Could not parse submission : missing parts or invalid data?")

    except Exception, e:
        et, val, tb = sys.exc_info()
        trace = traceback.format_tb(tb)
        error = "Exception : %s %s %s" % (et, val, trace[0])
        for tbm in trace:
            logging.error(tbm)
        response = json_fail(error)
    return render_json_response(response)

class BinaryChunkSubmitForm(forms.Form):
    """Form for submitting binary content in packetized form.
    
    ============== ================================
    Label          Description 
    ============== ================================
    procedure_guid the phone generated encounter id
    element_id     the element within the encounter for which the binary 
                   was recorded
    element_type   the type attribute of the parent element
    binary_guid    the comma separated value from the parent element
                   answer attribute for this binary
    file_size      the total size of the binary
    byte_start     the offset from the start of the file for this chunk
    byte_end       byte_start + chunk size(deprecated)
    byte_data      the chunk that will be written 
    ============== ================================
    
    :Authors: Sana dev team
    :Version: 1.1
    """
    procedure_guid = forms.CharField(required=True, max_length=512)
    element_id = forms.CharField(required=True)
    element_type = forms.CharField(required=True)
    binary_guid = forms.CharField(required=True)
    file_size = forms.IntegerField(required=True)
    byte_start = forms.IntegerField(required=True)
    byte_end = forms.IntegerField(required=True)
    byte_data = forms.FileField(required=True)
    done = forms.BooleanField(initial=False, required=False)

@enable_logging
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
    form = BinaryChunkSubmitForm(request.POST, request.FILES)

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
                response = json_succeed("Successfully saved binary chunk: %s" 
                                        % message)
            else:
                response = json_fail("Failed to save the binary chunk: %s" 
                                     % message)
        except Exception, e:
            et, val, tb = sys.exc_info()
            trace = traceback.format_tb(tb)
            error = "Exception : %s %s %s" % (et, val, trace[0])
            for tbm in trace:
                logging.error(tbm)
            response = json_fail(error)
        logging.info("Finished processing binarychunk form")
    else:
        logging.error("Received invalid binarychunk form")
        for k,v in request.REQUEST.items():
            if k == 'byte_data':
                logging.debug("%s:(binary length %d)" % (k,len(v)))
            else:
                logging.debug("%s:%s" % (k,v))
        response = json_fail("Invalid form: %s" % form.errors)
    return render_json_response(response)

class BinaryChunkHackSubmitForm(forms.Form):
    """Form for submitting binary content encoded as base64 text in packetized 
    form.
    
    ============== ================================
    Label          Description 
    ============== ================================
    procedure_guid the phone generated encounter id
    element_id     the element within the encounter for which the binary 
                   was recorded
    element_type   the type attribute of the parent element
    binary_guid    the comma separated value from the parent element
                   answer attribute for this binary
    file_size      the total size of the binary
    byte_start     the offset from the start of the file for this chunk
    byte_end       byte_start + chunk size(deprecated)
    byte_data      the chunk that will be written 
    ============== ================================
    
    :Authors: Sana dev team
    :Version: 1.1
    """
    procedure_guid = forms.CharField(required=True, max_length=512)
    element_id = forms.CharField(required=True)
    element_type = forms.CharField(required=True)
    binary_guid = forms.CharField(required=True)
    file_size = forms.IntegerField(required=True)
    byte_start = forms.IntegerField(required=True)
    byte_end = forms.IntegerField(required=True)

    byte_data = forms.CharField(required=True)
    #byte_data = forms.FileField(required=True)
    done = forms.BooleanField(initial=False, required=False)


@enable_logging
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
    form = BinaryChunkHackSubmitForm(request.POST, request.FILES)

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
                response = json_succeed("Successfully saved the binary chunk: %s" % message)
            else:
                response = json_fail("Failed to save the binary chunk: %s" % message)
        except Exception, e:
            logging.error("registering binary chunk failed: %s" % e)
            response = json_fail("Registering binary chunk failed: %s" % e)
        logging.info("Finished processing binarychunk form")
    else:
        logging.error("Received invalid binarychunk form")
        for k,v in request.REQUEST.items():
            if k == 'byte_data':
                logging.debug("%s:(binary length %d)" % (k,len(v)))
            else:
                logging.debug("%s:%s" % (k,v))
        response = json_fail("Invalid form: %s" % form.errors)

    logging.info("Sending response %s" % response)
    return render_json_response(response)


class BinarySubmitForm(forms.Form):
    """Form for submitting binary content encoded as base64 text in packetized 
    form.
    
    ============== ================================
    Label          Description 
    ============== ================================
    procedure_guid the phone generated encounter id
    element_id     the element within the encounter for which the binary 
                   was recorded
    ============== ================================
    
    :Authors: Sana dev team
    :Version: 1.1
    """
    procedure_guid = forms.CharField(required=True, max_length=512)
    element_id = forms.CharField(required=True)
    #data = forms.FileField(required=True)

@enable_logging
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

        response = json_succeed("Successfully saved the binary")
        logging.info("Done processing Binary submission form")
    else:
        logging.info("Received an invalid Binary submission form")
        response = json_fail("Could not parse submission. Missing parts?")

    return render_json_response(response)


class OpenMRSQueryForm(forms.Form):
    """A generic OpenMRS form with authorization information.
    
    :Authors: Sana dev team
    :Version: 1.1
    """
    username = forms.CharField(required=True, max_length=256)
    password = forms.CharField(required=True, max_length=256)

@enable_logging
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
        response = json_succeed(data)
    except Exception, e:
        et, val, tb = sys.exc_info()
        trace = traceback.format_tb(tb)
        error = "Exception : %s %s %s" % (et, val, trace[0])
        for tbm in trace:
            logging.error(tbm)
        logging.error("Got exception while fetching patient list: %s" % e)
        response = json_fail("Problem while getting patient list: %s" % e)
    return render_json_response(response)

@enable_logging
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
        response = json_succeed(data)
    except Exception, e:
        et, val, tb = sys.exc_info()
        trace = traceback.format_tb(tb)
        error = "Exception : %s %s %s" % (et, val, trace[0])
        for tbm in trace:
            logging.error(tbm)
        response = json_fail("couldn't get patient %s" % error)
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

def send_notification(n, phoneId):
    """Sends sms notification
    
    Parameters:
        n
            The notification.
        phoneId
            Phone number
    """
    # if phoneId == "emulator":
#         return send_fake_notification(n, phoneId)
#     else:

    # return send_clickatell_notification(n, phoneId)
    # return send_znisms_notification(n, phoneId)
    return send_kannel_notification(n, phoneId) # New default


SMS_MESSAGE_SIZE = 140
def format_sms(n):
    """Splits a given notification over a number of SMS messages and attaches
    header information for tracking which message is which. Returns a list of
    strings that are no more than SMS_MESSAGE_SIZE characters long.
    
    Parameters:
        n
            The notfication.
    """
    encoder = simplejson.JSONEncoder(separators=(',',':'))

    data = {'n': n.id,
            'c': n.procedure_id,
            'p': n.patient_id}
    subsequent_data = {'n': n.id,
                       'd': ''}
    test = encoder.encode(data)
    test_subsequent = encoder.encode(subsequent_data)

    # We have to clean the message of all uses of right-brace, because the
    # client will look for the last right brace in the text to find where the
    # JSON header ends. Just replace all left and right braces with parens.
    cleaned_message = n.message.replace("}",")").replace("{","(")

    # Search for the largest number of messages that fit.
    satisfied = False
    messages = 0

    while not satisfied:
        messages += 1
        message = cleaned_message
        message_size = len(message)
        result = []

        if messages > 1:
            data['d'] = '%d/%d' % (1,messages)
        header = encoder.encode(data)
        header_remaining = SMS_MESSAGE_SIZE - len(header)

        if header_remaining < 0:
            raise ValueError("Can't fit message.")

        header_message = message[:header_remaining]
        message = message[header_remaining:]
        result.append(header + header_message)

        for i in xrange(2, messages+1):
            subsequent_data['d'] = '%d/%d' % (i,messages)
            subsequent_header = encoder.encode(subsequent_data)
            subsequent_remaining = SMS_MESSAGE_SIZE - len(subsequent_header)
            subsequent_message = message[:subsequent_remaining]
            message = message[subsequent_remaining:]
            result.append(subsequent_header + subsequent_message)

        if len(message) == 0:
            satisfied = True

    return result

def send_clickatell_notification(message_body, phoneId):
    """Sends an SMS message to Clickatell http interface
        
    See Clickatell API documentation for full details. 
    
    Clickatell params
        user 
            Clickatell account user name
        password
            Clickatell account password
        api_id
            see Clickatell documentation
        to
            Recipient telephone number
        text
            Message Body
        
    Clickatell url: http://api.clickatell.com/http/sendmsg?params
    
    Parameters:
        message_body
            Message body
        phoneId
            Recipient
    """
    result = False
    try:
        messages = format_sms(message_body)
        for message in messages:

            params = urllib.urlencode({
                    'user': settings.CLICKATELL_USER,
                    'password': settings.CLICKATELL_PASSWORD,
                    'api_id': settings.CLICKATELL_API,
                    'to': phoneId,
                    'text': message
                    })

            logging.info("Sending clickatell notification %s to %s" %
                         (message, phoneId))
            response = urllib.urlopen(settings.CLICKATELL_URI % params).read()
            logging.info("Clickatell response: %s" % response)
            result = True
    except Exception, e:
        logging.error("Couldn't submit Clickatell notification for %s: %s" % (phoneId, e))
    return result

def send_znisms_notification(message_body, phoneId):
    """Sends an SMS message to ZniSMS http interface
        
    ZniSMS API documentation: http://www.znisms.com/api.pdf
        
    ZniSMS url: http://api.znisms.com/post/smsv3.asp?userid=joinus&apikey=xxx&
    message=Your+Message&senderid=9123123456&sendto=9123123457
        
    ZniSMS Request params
        userid     
            ZniSMS username
        apikey
            ZniSMS API key
        message
            SMS message body to send
        senderid
            Sender ID (should be alphanumeric)
        sendto
            Destination number (no +91, 91 or 0 in front)
        
    Parameters:
        message_body
            Message body
        phoneId
            Recipient
    """
    result = False
    try:
        messages = format_sms(message_body)
        for message in messages:

            params = urllib.urlencode({
                    'userid': settings.ZNISMS_USER,
                    'apikey': settings.ZNISMS_APIKEY,
                    'senderid': settings.ZNISMS_SENDERID,
                    'sendto': phoneId,
                    'message': message
                    })

            logging.info("Sending ZniSMS notification %s to %s" %
                         (message, phoneId))
            response = urllib.urlopen(settings.ZNISMS_URL % params).read()
            logging.info("ZniSMS response: %s" % response)
            result = True
    except Exception, e:
        logging.error("Couldn't submit ZniSMS notification for %s: %s" % (phoneId, e))
    return result

def send_fake_notification(n, phoneId):
    """Sends a fake SMS via telnet
    
    Parameters:
        n
            The notification
        PhoneId
            a phone number
    """
    try:
        message = "<patient=%s>Patient %s : %s" % (n.patient_id, n.patient_id, n.message)
        print "Sending", message
        t = telnetlib.Telnet('127.0.0.1', 5554)
        t.read_until("OK")

        # needs to be str not unicode?
        #cmd = str("sms send %s %s\n" % (n.client, message))
        cmd = "sms send %s %s\n" % ("3179461787", str(message).replace("\n",""))
        #cmd = "sms send %s \"%s\"\n" % (str(n.client), str(n.to_json()))
        #logging.error(cmd)
        t.write(str(cmd))
        t.read_until("OK")
        t.write("exit\n")
        t.close()

        n.delivered = True
        n.save()
    except Exception, e:
        n.delivered = False
        n.save()
        logging.error("Couldn't submit notification for %s" % str(e))

@enable_logging
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

    response = json_fail('Failed to register notification.')
    if phoneId and text and caseIdentifier and patientIdentifier:
        n = Notification(client=phoneId,
                         patient_id=patientIdentifier,
                         message=text,
                         procedure_id=caseIdentifier,
                         delivered=delivered)
        n.save()
        try:
            delivered = send_notification(n, phoneId)
            response = json_succeed('Successfully sent notification.')
        except Exception, e:
            logging.error("Got error while trying to send notification: %s" % e)
            response = json_succeed('Failed to send notification. Error')
            
    return render_json_response(response)

@enable_logging
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

    response = json_fail('Failed to register email notification.')

    try:
        emailAddresses = cjson.decode(addresses)
    except Exception, e:
        response = json_fail('Got error when trying to parse email addresses.')

    if addresses and caseIdentifier and patientId:
        try:
            send_mail(subject, message, settings.OPENMRS_REPLYTO,
                          emailAddresses, fail_silently=False)
            response = json_succeed('Successfully registered email notification')
        except Exception, e:
            logging.error('Email could not be sent: %s' % e)
    return render_json_response(response)

@enable_logging
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
        return render_json_response(json_fail("Could not parse eventlog submission."))

    logging.info("Received events parameter: %s" % events_json)

    try:
        events = simplejson.loads(events_json)
        result, message = register_client_events(client_id, events)

        response = None
        if result:
            response = json_succeed(message)
        else:
            response = json_fail(message)
    except Exception, e:
        logging.error("Error while processing events: %s" % e)
        response = json_fail("Could not parse eventlog submission.")
    return render_json_response(response)

def send_kannel_notification(n, phoneId):
    """Sends a notification to a phone as one or more sms messages through a
    Kannel SMS gateway.
    
    Parameters:    
        n
            The message body
        phoneId
            The recipient
    """
    result = False
    try:
        messages = format_sms(n)
        for message in messages:
            params = urllib.urlencode({
                    'username': settings.KANNEL_USER,
                    'password': settings.KANNEL_PASSWORD,
                    'to': phoneId,
                    'text': message
                    })

            logging.info("Sending kannel notification %s to %s" %
                         (message, phoneId))
            response = urllib.urlopen(settings.KANNEL_URI % params).read()
            logging.info("Kannel response: %s" % response)
            result = True
    except Exception, e:
        logging.error("Couldn't submit Kannel notification for %s: %s" 
                      % (phoneId, e))
    return result

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
    
    
@enable_logging
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
        
        response = json_savedprocedure_succeed(saved_procedure.procedure_guid, 
                                               saved_procedure.encounter, 
                                               saved_procedure.responses)
    except Exception, e:
        logging.error("Got error %s" % e)
        response = json_fail("couldn't find encounter")
    logging.info("finished returning saved_procedure %s : %s : %s" 
                 % (saved_procedure.procedure_guid, saved_procedure.encounter, 
                    saved_procedure.responses))
    return render_json_response(response)


@enable_logging
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
        response = json_succeed(data)
    except Exception, e:
        logging.error("Got exception while fetching patient list: %s" % e)
        response = json_fail("Problem while getting patient list: %s" % e)
    return render_json_response(response)

@enable_logging
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
    response = json_succeed(procedure_guids, data)
    
    logging.info("finished sync_encounters")
    return render_json_response(response)



