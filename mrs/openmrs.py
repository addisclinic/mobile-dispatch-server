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
import sys, traceback
from urlparse import urlparse

import telnetlib

from django.conf import settings

from mrs import MultipartPostHandler
from mrs.util import enable_logging
from mrs.util import mark


class OpenMRS(object):
    """Utility class for remote communication with OpenMRS """

    def __init__(self, username, password, url):
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
        self.url = url

        self.cookies = cookielib.CookieJar()

        try:
            password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(None, self.url, self.username, self.password)
            auth_handler = urllib2.HTTPBasicAuthHandler(password_mgr)
            self.opener = urllib2.build_opener(
                auth_handler,
                urllib2.HTTPCookieProcessor(self.cookies),
                MultipartPostHandler.MultipartPostHandler)
        except Exception, e:
            print "Couldn't initialize openMRS interface, exception: " + str(e)

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
        try:
            loginParams = urllib.urlencode(
                {"uname": self.username,
                 "pw": self.password,
                 "redirect": "/openmrs",
                 "refererURL": self.url+"index.htm"
                 })
            result = self.opener.open("%sloginServlet" % self.url, loginParams)
            if result.geturl()==self.url + "index.htm":
                mark('openmrs', 61, result.code, self.url, result.geturl())
                return True
            else:
                return False
        except Exception, e:
            print("Exception validating credentials with OpenMRS: %s" % e)

    def validate_patient(self, patient_id):
        pass

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
                                      MultipartPostHandler.MultipartPostHandler)
        urllib2.install_opener(opener)
        rest = urllib2.urlopen(uri)
        return rest.read()

    def getAllPatients(self,username, password):
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
                                      MultipartPostHandler.MultipartPostHandler)
        urllib2.install_opener(opener)
        rest = urllib2.urlopen(uri)
        return rest.read()

    def create_patient(self, patient_id, first_name, last_name, gender,
                       birthdate):
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
                self._login()
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

    def _login(self):
        loginParams = urllib.urlencode(
            {"uname": self.username,
             "pw": self.password,
             "redirect": "/openmrs",
             "refererURL": self.url+"index.htm"
             })
        try:
            self.opener.open("%sloginServlet" % self.url, loginParams)
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

        except Exception as e:
            logging.error("Exception in uploading procedure: %s"
                          % saved_procedure_id)
            raise e
        return result, message, encounter

def download_procedure(self, encounter):
    # OpenMRS procedure retrieval goes here.
    # Recommend starting by making this return a test procedure.
    pass

def generateJSONDescriptionFromDict(responses, patientId, phoneId, procedureId):
    return cjson.encode(
        {'phoneId': str(phoneId),
         'patientId': str(patientId),
         'procedureId': str(procedureId),
         'questions': responses})

def sendToOpenMRS(patientId, phoneId, procedureId,
                  filePath, responses, username, password):
    """Sends procedure data to OpenMRS

    Expects:

        1. a valid patientId that is registered in OpenMRS already
        2. a file path to an image
        3. a QA dict of string question / answer pairs

    Parameters:
        patientId
            The patient id for this encounter
        phoneId
            The sending client id. Usually a telephone number.
        procedureId
            the id of the procedure used for collecting data
        filePath
            THe local path to files which will be uploaded.
        responses
            the data text collected
        username
            A username(for uploading).
        password
            A password(for uploading).
    """
    uploadToOpenMRS(
        patientId,
        filePath,
        generateJSONDescriptionFromDict(responses,
                                        patientId,
                                        phoneId,
                                        procedureId),
        settings.OPENMRS_SERVER_URL,
        username,
        password)


def uploadToOpenMRS(patientId, filePath, description, url, username, password):
    """Uploads a file to OpenMRS and tags it on a given patientId's
    'Medical Images' tab.

    Parameters:
        patientId
            The patientId is the internal patient ID in OpenMRS, NOT the
            "Identification Number" that one can search for in OpenMRS.
        filePath
            THe local path to files which will be uploaded.
        description
            The form data which will be sent. Does not need to be url-safe,
            since this method encodes it as such. Double-encoding it will
            produce non-desired output.
        url
            The OpenMRS url. ::

                http://myserver.com/openmrs/
        username
            A username(for uploading).
        password
            A password(for uploading).

    """
    cookies = cookielib.CookieJar()

    opener = urllib2.build_opener(
        urllib2.HTTPCookieProcessor(cookies),
        MultipartPostHandler.MultipartPostHandler)
    loginParams = urllib.urlencode(
        {"uname": username,
         "pw": password,
         "redirect": "/openmrs",
         "refererURL": url+"index.htm"
         })
    opener.open("%sloginServlet" % url, loginParams)
    for cookie in cookies:
        logging.debug("Cookie: %s" % cookie)
    getParams = urllib.urlencode({'patientIdentifier': str(patientId),
                                  'imageDate': time.strftime("%m/%d/%Y"),
                                  'description': str(description)})
    postParams = {"medImageFile": open(filePath, "rb")}
    postUrl = "%smoduleServlet/gmapsimageviewer/formImageUpload?%s" % (url, getParams)
    opener.open(postUrl, postParams)
    logging.debug("Done with upload")
