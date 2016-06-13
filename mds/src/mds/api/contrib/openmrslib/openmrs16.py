""" Classes and utilities for talking to an OpenMRS server

:Authors: Sana Dev Team
:Version: 1.1
"""
import urllib
import cookielib
import logging
import urllib2
import cjson
import time

from django.conf import settings
from mds.api.contrib import handlers
from mds.api.responses import succeed, fail

class OpenMRS(object):
    """Utility class for remote communication with OpenMRS """

    paths = {"sessions": "loginServlet",
             "session" : "moduleServlet/moca/permissionsServlet",
             "subject" : "moduleServlet/restmodule/api/patient/{uuid}",
             "subjects" : "moduleServlet/restmodule/api/allPatients/",
             "encounters" : "moduleServlet/sana/uploadServlet/",
             "patient": "admin/patients/newPatient.form",
             "session": "loginServlet"}
    
    def __init__(self, host, username=None, password=None):
        """Called when a new OpenMRS object is initialized.
            
        Parameters:
            username
                A valid user name for authoriztion
            password
                A valid user password for authorization
            url
                The OpenMRS host root url having the form::
                
                    http:<ip or hostname>[:8080 | 80]/openmrs/
                
                and defined in the settings.py module
        """
        self.username = username
        self.password = password
        self.url = host

        self.cookies = cookielib.CookieJar()

        try:
            password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(None, self.url, self.username, self.password)
            auth_handler = urllib2.HTTPBasicAuthHandler(password_mgr)
            self.opener = urllib2.build_opener(
                auth_handler,
                urllib2.HTTPCookieProcessor(self.cookies),
                handlers.MultipartPostHandler)
        except Exception, e:
            print "Couldn't initialize openMRS interface, exception: " + str(e)

    def wsdispatch(self, wsname, pargs={}, query=None, data=None, auth=None, 
                   response_handler=None):
        """ Dispatches a request to an upstream web service. 
            Limited capability implementation.

            session => auth
            subject => subject dict(see patient Form)
            subject => uuid dict
            subjects => auth dict
            encounter => encounter dict
            
            for keys to use in query or data 
        
        """
        if wsname == 'sessions':
            try:
                message = self.login(auth=auth)
                response = succeed(message)
            except Exception, e:
                response = fail(str(e))
            return response
        elif wsname == "subject":
            if data:
                patient_id = data.get("uuid")
                first_name = data.get("first_name")
                last_name = data.get("last_name")
                gender = data.get("gender")
                birthdate = data.get("birthdate")
                return self.create_patient(patient_id, first_name, last_name, gender, birthdate, auth=auth)
            else:
                return self.getPatient(auth.get("username"), auth.get("password"), query.get("uuid"))
        elif wsname == "subjects":
            return self.getAllPatients(auth.get("username"), auth.get("password"))
        elif wsname == "encounter":
            patient_id = data.get("subject")
            phone_id = data.get("device")
            procedure_title = data.get("procedure")
            saved_procedure_id = data.get("uuid")
            responses = data.get("observations")
            files = data.get("files")
            return self.upload_procedure(patient_id, phone_id, procedure_title, 
                                         saved_procedure_id, responses, files, 
                                         auth=auth)
        raise Exception("Unknown service")    

    
    def login(self, auth=None):
        if auth:
            self.username = auth.get("username","")
            self.passsword = auth.get("password","")
            
        loginParams = urllib.urlencode(
            {"uname": self.username,
             "pw": self.password,
             "redirect": "/openmrs",
             "refererURL": self.url+"index.htm"
             })
        
        response = self.opener.open("%sloginServlet" % self.url, loginParams)
        logging.debug("Success: Validating with OpenMRS loginServlet")
        
        if response.geturl()==self.url + "index.htm":
            return u"username and password validated!"
        else:
            raise Exception(u"username and password combination incorrect!")

    def validate_credentials(self, username, password):
        """Validates OpenMRS authorization for a user by sending a POST request 
        to the loginServlet( self.url + loginServlet)
           
        The following request parameters are sent: ::
            
            Parameter     OpenMRS form field   Default Value
            username      uname                N/A
            password      pw                   N/A
            N/A           redirect             /openmrs
            N/A           refererURL           self.url+index.htm
            
        Parameters:
            username
                a valid username
            password
                a valid password
        """
        loginParams = urllib.urlencode(
                {"uname": self.username,
                 "pw": self.password,
                 "redirect": "/openmrs",
                 "refererURL": self.url+"index.htm"
                 })
        result = self.opener.open("%sloginServlet" % self.url, loginParams)
        if result.geturl()==self.url + "index.htm":
            return u"username and password validated!"
        else:
            raise Exception(u"username and password combination incorrect!")
    
    def getPatient(self,username, password, userid):
        """Retrieves a patient by id from OpenMRS through the REST module.

        OpenMRS url: <host> + moduleServlet/restmodule/api/patient/+userid
        
        Parameters:
            username
                OpenMRS username
            password
                OpenMRS password
            userid
                patient identifier
           
        """
        uri = self.url+'moduleServlet/restmodule/api/patient/'+userid

        cookies = cookielib.CookieJar()
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, uri, username, password)
        auth_handler = urllib2.HTTPBasicAuthHandler(password_mgr)
        opener = urllib2.build_opener(auth_handler,
                                      urllib2.HTTPCookieProcessor(cookies),
                                      handlers.MultipartPostHandler)
        urllib2.install_opener(opener)
        rest = urllib2.urlopen(uri)
        return rest.read()
    
    def getAllPatients(self,username, password, query=None):
        """Retrieves all patients from OpenMRS through the REST module.

        OpenMRS url: <host> + moduleServlet/restmodule/api/allPatients/
        
        Parameters:
            username
                OpenMRS username
            password
                OpenMRS password
            userid
                patient identifier
           
        """
        uri = self.url+'moduleServlet/restmodule/api/allPatients/'
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, uri, username, password)
        auth_handler = urllib2.HTTPBasicAuthHandler(password_mgr)
        opener = urllib2.build_opener(auth_handler,
                                      urllib2.HTTPCookieProcessor(self.cookies),
                                      handlers.MultipartPostHandler)
        urllib2.install_opener(opener)
        rest = urllib2.urlopen(uri)
        return rest.read()
    
    def create_patient(self, patient_id, first_name, last_name, gender, 
                       birthdate, auth=None):
        """Sends a post request to OpenMRS patient service to create patient.
                
        OpenMRS url: <host> + admin/patients/newPatient.form
           
        OpenMRS Form Fields: ::
        
            Parameters    OpenMRS form field    Note
            first_name    name.givenName        N/A
            last_name     name.familyName       N/A
            patient_id    identifier            N/A
            gender        gender                M or F
            birthdate     birthdate             single digits must be padded            
            N/A           identifierType        use "2"
            N/A           location              use "1"
        
        Parameters:
            patient_id
                client generated identifier
            first_name
                patient given name
            last_name
                patient family name
            gender
                M or F
            birthdate
                patient birth date formatted as mm/dd/yyyy
        """
        try:
            if len(self.cookies) == 0:
                self.login(auth=auth)
            parameters = {"name.givenName": first_name,
                          "name.familyName": last_name,
                          "identifier": patient_id,
                          "identifierType": 2,
                          "location": 1,
                          'gender': gender,
                          'birthdate': birthdate,}
            #parameters = urllib.urlencode(parameters)
            url = "%sadmin/patients/newPatient.form" % self.url
            logging.info("Creating new patient %s" % patient_id)
            self.opener.open(url, parameters)
        except Exception, e:
                logging.info("Exception trying to create patient: %s" % str(e))

    
    def upload_procedure(self, patient_id, phone_id,
                         procedure_title, saved_procedure_id,
                         responses, files, auth=None):
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
                self.login(auth=auth)
    
            logging.debug("Validating permissions to manage sana queue")

            url = "%smoduleServlet/moca/permissionsServlet" % self.url
            response = self.opener.open(url).read()
            logging.debug("Got result %s" % response)
            resp_msg = cjson.decode(response,True)
            message = resp_msg['message']
            hasPermissions = True if resp_msg['status'] == 'OK' else False
            if not hasPermissions:
                return result, message
            
            logging.debug("Uploading procedure")
            # NOTE: Check version format in settings matches OpenMRS version
            description = {'phoneId': str(phone_id),
                           'procedureDate': time.strftime(
                                                    settings.OPENMRS_DATE_FMT),
                           'patientId': str(patient_id),
                           'procedureTitle': str(procedure_title),
                           'caseIdentifier': str(saved_procedure_id),
                           'questions': responses}
            
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

            url = "%smoduleServlet/moca/uploadServlet" % self.url
            logging.debug("About to post to " + url)
            response = self.opener.open(url, post).read()
            logging.debug("Got result %s" % response)
                
            resp_msg = cjson.decode(response,True)
            message = resp_msg.get('message', '')
            result = True if resp_msg['status'] == 'OK' else False
            encounter = resp_msg.get('encounter', None)
            logging.debug("Done with upload")
            
        except Exception, e:
            logging.error("Exception in uploading procedure: %s" 
                          % saved_procedure_id)
            raise
        return result, message, encounter

def generateJSONDescriptionFromDict(responses, patientId, phoneId, procedureId):
    return cjson.encode(
        {'phoneId': str(phoneId),
         'patientId': str(patientId),
         'procedureId': str(procedureId),
         'questions': responses})
