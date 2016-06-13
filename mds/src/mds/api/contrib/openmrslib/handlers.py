""" Classes and utilities for talking to an OpenMRS server version 1.9

:Authors: Sana Dev Team
:Version: 2.0
"""
import urllib
import cookielib
import logging
import urllib2
import cjson
import time
import base64
import datetime

from django.conf import settings

from .openers import OpenMRSOpener
from .models import *
from . import rest_api
from mds.api.responses import succeed, fail
from mds.core.models import Subject

__all__ = [
    'OpenMRSHandler',
]


SESSION_STATUS = "authenticated"
SESSION_INVALID = u"Invalid auth data" 
SESSION_CONTENT = "sessionId"
LIST_CONTENT  = "results"
ERROR_CONTENT = "error"
ERROR_MESSAGE = "message"
ERROR_SOURCE = "code"


def error_reader(response, all_unicode=False):
    message = response[ERROR_CONTENT][ERROR_MESSAGE]
    return fail(message)

def resultlist_reader(response, all_unicode=False):
    """ Returns a list
    """
    links = []
    def get_self(links):
        for link in links:
            if link['rel'] == "self":
                return link['uri']
            
    for result in response:
        links.append(get_self(result['links']))
    return links

def item_reader(response, reader=None, all_unicode=False):
    pass

def rest_reader(response, reader=None, decoder=None, all_unicode=True):
    msg = cjson.decode(response, all_unicode=all_unicode)
    logging.debug('Response object type: %s' % type(msg))
    logging.debug('Response object type is dict: %s' % isinstance(msg,dict))
    result = None
    if ERROR_CONTENT in msg:
        return error_reader(msg)
    # POST calls and session opens return a dict
    elif SESSION_CONTENT in msg:
        return session_reader(response)
    elif LIST_CONTENT in msg:
        content = msg[LIST_CONTENT]
        if decoder:
            return [decoder.decode(x) for x in content]
        elif reader:
            return [reader(x) for x in content]
        else:
            return resultlist_reader(content)
    else:
        # Just get a single object back on a post
        logging.debug("REST API returned single object")
        if decoder:
            result = decoder.decode(msg)
            return result
        elif reader:
            return reader(msg)

def session_reader(response, all_unicode=False):
    """ Returns a succeed or fail response dict with the message content set to 
        the session id or an error message.
    """
    msg = response
    if msg.get(SESSION_STATUS, False):
        return succeed(msg.get(SESSION_CONTENT))
    
    else:
        return fail(SESSION_INVALID)

def login_form(host, username, password):
    return {"uname": username,
             "pw": password,
             "redirect": "/openmrs",
             "refererURL": host+"index.htm"
             }

def patient_form(first_name, last_name, patient_id, gender, birthdate):
    """OpenMRS Short patient form for creating a new patient.  
    
            Parameters    OpenMRS form field            Note
            first_name    personName.givenName          N/A
            last_name     personName.familyName         N/A
            patient_id    identifiers[0].identifier     N/A
            gender        patient.gender                M or F
            birthdate     patient.birthdate             single digits must be padded            
            N/A           identifiers[0].identifierType use "2"
            N/A           identifiers[0].location       use "1"
    """
    data = {"personName.givenName": first_name,
            "personName.familyName": last_name,
            "identifiers[0].identifier": patient_id,
            "identifiers[0].identifierType": 2,
            "identifiers[0].location": 1,
            "patient.gender": gender,
            "patient.birthdate": birthdate,}
    return data

def person_form(**data):
    pass

def encounter_queue_form(patient_id, phone_id,
                         procedure_title, saved_procedure_id,
                         responses):
    description = {'phoneId': str(phone_id),
                   'procedureDate': time.strftime(settings.OPENMRS_DATE_FMT),
                   'patientId': str(patient_id),
                   'procedureTitle': str(procedure_title),
                   'caseIdentifier': str(saved_procedure_id),
                   'questions': responses}
    return description

def queue_form(encounter):
    pass
    

class OpenMRSHandler(OpenMRSOpener):
    """ Utility class for remote communication with OpenMRS version 1.9
        
        Notes for the OpenMRS Webservices.REST API;
        1. 'There is a filter defined on the module that intercepts all calls and 
        authenticates the given request. 

        Currently only BASIC authentication is supported.  Header arguments 
        values of __ and __ are expected.
        
        Alternatively, a session token can be used.  
            GET /openmrs/ws/rest/$VERSION/session 
        with the BASIC credentials will return the current token value.  This 
        token should be passed with all subsequent calls as a cookie named 
        "jsessionid=token".'
        
        Sana developer comments:
        For BASIC Credentials the following snippet will open a resource:
        
        # url, username, and password as appropriate
        cookies = cookielib.CookieJar()
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, url, username, password)
        auth_handler = urllib2.HTTPBasicAuthHandler(password_mgr)
        opener = urllib2.build_opener(auth_handler,
                urllib2.HTTPCookieProcessor(cookies),)
        urllib2.install_opener(opener)
        
        # Build a request and set the headers
        req = urllib2.Request(url)
        basic64 = lambda x,y: base64.encodestring('%s:%s' % (x, y))[:-1]
        req.add_header("Authorization", "Basic %s" % basic64(username, password))
        opener.open(req)
        
        For session access:
        A successful GET sent to the session resource path:
            /openmrs/ws/rest/$VERSION/session ($VERSION is 'v1' for OpenMRS 1.8-1.9)
        will return:        
        
        {"sessionId":"E77D1DEACFEAF53282D9453603005A3D","authenticated":true}
        
        You will need to set the 
        # This will add 
        authenticated = session.get("authenticated",False)
        jsessionid = session.get("sessionId")
        req = urllib2.Request(url)
        req.add_header("jsessionid", jsessionid)
        return opener.open(req)
        
        
        
        2. REST Resources
        See:
            https://wiki.openmrs.org/display/docs/REST+Web+Service+Resources
        
    """
    
    paths = {"sessions": "ws/rest/v1/session/",
             "session": "ws/rest/v1/session/{uuid}",
             "concept" : "ws/rest/v1/concept/{uuid}",
             "concepts" : "ws/rest/v1/concept/",
             "person" : "ws/rest/v1/person/{uuid}",
             "person-create" : "ws/rest/v1/person/",
             "persons" : "ws/rest/v1/person/",
             "subject" : "ws/rest/v1/patient/{uuid}",
             "subject-create" : "ws/rest/v1/patient/",
             "subjects" : "ws/rest/v1/patient/",
             "sana-encounters" : "moduleServlet/sana/uploadServlet",
             "encounters" : "ws/rest/v1/encounter/",
             "encounter" : "ws/rest/v1/encounter/{uuid}",
             "encounter_observations": "ws/rest/v1/encounter/{uuid}/observation/",
             "patient": "admin/patients/shortPatientForm.form",
             "users": "ws/rest/v1/user/",
             "user": "ws/rest/v1/user/{uuid}",
             "login": "loginServlet"}

    forms = {"patient": patient_form,
               "login": login_form }

    def open(self, url, username=None, password=None, **kwargs):
        opener, session = self.open_session(username, password)
        if not session["authenticated"]:
            raise Exception(u"username and password combination incorrect!")
        
        # short circuit here
        if url ==  self.build_url("sessions"):
            return u"username and password validated!"
        jsessionid = session.get("sessionId")
        req = urllib2.Request(url)
        req.add_header("jsessionid", jsessionid)
        if kwargs:
            data = kwargs.get('data',kwargs)
            postdata = cjson.encode(data)
            req.add_header('Accept','application/json')
            req.add_header('Content-type','application/json')
            req.add_data(postdata)
        logging.debug("Dispatching request")
        logging.debug("...url: %s" % req.get_full_url())
        logging.debug("...method: %s" % req.get_method())
        return opener.open(req)
    
    def open_session(self, username=None, password=None):
        logging.debug("Opening session")
        url = self.build_url("sessions")
        cookies = cookielib.CookieJar()
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, url, username, password)
        auth_handler = urllib2.HTTPBasicAuthHandler(password_mgr)
        opener = urllib2.build_opener(auth_handler,
                urllib2.HTTPCookieProcessor(cookies),)
        urllib2.install_opener(opener)
        req = urllib2.Request(url)
        basic64 = lambda x,y: base64.encodestring('%s:%s' % (x, y))[:-1]
        if username and password:
            req.add_header("Authorization", "Basic %s" % basic64(username, password))
        session = cjson.decode(opener.open(req).read())
        return opener, session
    
    def getPatient(self,username, password, patientid):
        """ Retrieves a patient by id from OpenMRS through the Webservices.REST 
            module.
            
            Backwards compatibility method.
        """
        wsname = 'subjects' 
        pargs={"q":patientid,
               "v":"full" }
        auth = {"username": username,
                 "password": password }
        logging.debug("query" % pargs)
        response = self.wsdispatch(wsname, query=pargs, response_handler=patient_reader, auth=auth)
        logging.debug("response: %s" % response)
        content = response
        return content
    
    def getAllPatients(self,username, password, query=None):
        """Retrieves all patients from OpenMRS through the REST module.
        
        Backwards compatibility method.
        """
        
        wsname = 'subjects' 
        auth = {"username": username,
                 "password": password }
        
        response = self.wsdispatch(wsname, query=query, response_handler=patient_reader, auth=auth)
        logging.debug(response)
        content = []
        for uri in response:
            person = cjson.decode(self.open(uri+"?v=full", username, password).read())

            patient = {}
            name = person["names"]
            patient['first_name'] = name["givenName"]
            patient['family_name'] = name["familyName"]
            patient['gender'] = person["gender"]
            patient['birthdate'] = person["birthdate"]
            patient['uuid'] = person["uuid"]
            content.append(patient)
        return content
    
    def create_patient(self, patient_id, first_name, last_name, gender, 
                       birthdate, auth=None):
        """ (Deprecated)Sends a post request to OpenMRS patient service to 
            create patient.
        """
        data = patient_form(patient_id, first_name, last_name, gender, 
                       birthdate)
        pargs={"uuid":"" }
        response = self.wsdispatch("patient", pargs=pargs, auth=auth, data=data)
        return response

    def _login(self, username=None, password=None):
        data = login_form(self.host, username, password)
        try:
            self.opener.open("%sloginServlet" % self.host, data)
            logging.debug("Success: Validating with OpenMRS loginServlet")
            result = True
        except Exception, e:
            logging.debug("Error logging into OpenMRS: %s" % e)
            result = False
        return result
    
    def upload_procedure(self, patient_id, phone_id,
                         procedure_title, saved_procedure_id,
                         responses, files):
        """Posts an encounter to the OPenMRS encounter service through the Sana
        module
        
        OpenMRS url: <host> + moduleServlet/moca/uploadServlet
        
        OpenMRS Form Fields: ::
        
            Parameter             OpenMRS form field    Note
            phone_id              phoneId
                                  procedureDate         mm/dd/yyyy
            patient_id            patientId
            procedure_title       procedureTitle
            saved_procedure_id    caseIdentifier
            responses             questions
            
        Note: Above parameters are then encoded and posted to OpenMRS as the
        'description' field value.
            
        Binaries are attached as one parameter per binary with field name
        given as 'medImageFile-<element-id>-<index> where index correlates 
        to the position in the csv 'answer' attribute of the particular 
        procedure element
        
        Parameters:
            phone_id
                client telephone number.     
            patient_id   
                The patient identifier.
            procedure_title
                The procedure tirle.
            saved_procedure_id
                Saved procedure id.
            responses
                Encounter text data as JSON encoded text.
        """
        hasPermissions = False 
        result = False
        message = ""
        encounter = None
        response = None
        try:
            if len(self.cookies) == 0:
                self._login()
    
            logging.debug("Validating permissions to manage sana queue")

            url = "%smoduleServlet/sana/permissionsServlet" % self.url
            response = self.opener.open(url).read()
            logging.debug("Got result %s" % response)
            resp_msg = cjson.decode(response,True)
            message = resp_msg['message']
            hasPermissions = True if resp_msg['status'] == 'OK' else False
            if not hasPermissions:
                return result, message
            
            logging.debug("Uploading procedure")
            # NOTE: Check version format in settings matches OpenMRS version
            description = encounter_queue_form(patient_id, phone_id,
                         procedure_title, saved_procedure_id,
                         responses)
            
            description = cjson.encode(description)
            post = {'description': str(description)}
            logging.debug("Encoded parameters, checking files.")
            # Attach a file 
            for elt in responses:
                etype = elt.get('type', None)
                eid = elt.get('id', None)
                if eid in files:
                    logging.info("Checking for files associated with %s" % eid)
                    for i,path in enumerate(files[eid]):
                        logging.info('medImageFile-%s-%d -> %s' 
                                     % (eid, i, path))
                        post['medImageFile-%s-%d' % (eid, i)] = open(path, "rb")

            url = "%smoduleServlet/sana/uploadServlet" % self.url
            logging.debug("About to post to " + url)
            response = self.opener.open(url, post).read()
            logging.debug("Got result %s" % response)
                
            resp_msg = cjson.decode(response,True)
            message = resp_msg.get('message', '')
            result = True if resp_msg['status'] == 'OK' else False
            encounter = resp_msg.get('encounter', None)
            logging.debug("Done with upload")
            
        except Exception as e:
            logging.error("Exception in uploading procedure: %s" 
                          % saved_procedure_id)
            raise e
        return result, message, encounter
    
    def create_subject(self, instance, auth=None):
        '''
        content =  self.create_patient(
            instance.system_id, 
            instance.given_name,
            instance.family_name, 
            instance.gender, 
            instance.dob, 
            auth=auth)
        '''
        data = m_subject.encode(instance)
        wsname = 'subject-create'
        response = self.wsdispatch(wsname, data=data, auth=auth)
        result = rest_reader(response, decoder=m_subject)
        logging.info("POST success to OpenMRS %s" % result)
        return result

    def read_subject(self, instance, auth=None):
        wsname = 'subjects'
        query = { 'q' : instance.system_id }
        response = self.wsdispatch(wsname, query=query, auth=auth)
        result = rest_reader(response, decoder=m_subject)
        return result

    def create_session(self, instance, auth=None):
        ''' Assumes openmrs is credential authority. Checks for
            presence of OpenMRS user and returns an instnace of 
            Observer object with the new auth.User. This method does
            not persist new user or observer.
        '''
        logging.info('create_session')
        username = auth.get('username') if auth else None
        pargs = {'q':username, 'v': 'default' }
        response = self.wsdispatch('users', query=pargs, auth=auth)
        rest_response = rest_api.decode(response, result_decoder=m_observer)
        # REST api will return if person name or username match here
        # so we have to iterate
        result = None
        for obj in rest_response.results:
            result = obj if obj.user.username == username else None
            if result:
                break
        # Shouldn't happen but just in case we get
        if not result:
            raise Exception('No precise username match')
        return result

