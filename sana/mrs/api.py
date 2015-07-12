"""Utilities for processing requests

:Authors: Sana Dev Team
:Version: 1.1
"""
from __future__ import with_statement
import os, sys, traceback
import cjson
import datetime
import logging
from collections import defaultdict

from django.conf import settings

from sana.mrs.models import SavedProcedure, Client, BinaryResource, ClientEventLog
from sana.mrs import openmrs
from sana.mrs.media import FFmpeg
from sana.mrs.util import flush, mark

# api.py -- interface-agnostic API methods

BINARY_TYPES = ['PICTURE', 'SOUND', 'VIDEO', 'BINARYFILE']
"""Element types that may include file data."""

BINARY_TYPES_EXTENSIONS = {
    'PICTURE': 'jpg',
    'SOUND': '3gp',
    'VIDEO': '3gp',
    'BINARYFILE': 'mpg',}
"""File extensions for the binary types."""

CONTENT_TYPES = {
    'PICTURE': 'image/jpeg',
    'SOUND': 'audio/3gpp',
    'VIDEO': 'video/3gpp',
    'BINARYFILE': 'video/mpeg'}
"""Mime types for client content."""
#'BINARYFILE': 'application/octet-stream'}

CONVERTED_BINARY_TYPES_EXTENSIONS = {
    'SOUND': 'mp3',
    'VIDEO': 'flv',}
"""File extensions for transcoded files."""

CONVERTED_CONTENT_TYPES = {
    'SOUND': 'audio/mpeg',
    'VIDEO': 'video/x-flv'}
"""Mime types of files that will be uploaded."""

DEFAULT_PATIENT_ID = "500"

months_dict = {'January':'01',
               'February':'02',
               'March':'03',
               'April':'04',
               'May':'05',
               'June':'06',
               'July':'07',
               'August':'08',
               'September':'09',
               'October':'10',
               'November':'11',
               'December':'12'}
"""Month name to two character numeric string mapping."""

def register_saved_procedure(sp_guid, procedure_guid, responses,
                             client_id, username, password):
    '''
    Registers a new saved procedure as well as looks up an existing one.

    Parameters:
        sp_guid
            the id of this encounter
        procedure_guid
            the id of the procedure used for collecting data
        responses
            the data text collected
        client_id
            The sending client id. Usually a telephone number.
        username
            A username(for uploading).
        password
            A password(for uploading).

        Note: There is a naming inconsistency between this method and others in
        this module with respect to the use of procedure_guid
    '''
    logging.info('Registering saved procedure %s' % sp_guid)
    logging.debug('sp_guid -> %s, client_id -> %s, responses -> %s'
                  % (sp_guid,responses,client_id))
    client,_ = Client.objects.get_or_create(name=client_id)
    client.save()
    sp, created = SavedProcedure.objects.get_or_create(guid=sp_guid, client=client)
    sp.procedure_guid=procedure_guid
    sp.client=client

    # Block all other threads from acquiring this saved procedure
    if not created:
        logging.warning('SavedProcedure -> %s exists. unstable connection?'
                        % sp_guid)
    sp.upload_username = username
    sp.upload_password = password
    sp.responses = responses
    sp.save()

    # Read through responses and create BinaryResources if type is in
    # BINARY_TYPES above
    try:
        responses_dict = cjson.decode(responses,True)
        for k,v in responses_dict.items():
            if settings.DEBUG:
                logging.debug("%s : %s" % (k,v))
            if v['type'] in BINARY_TYPES:
                items = v['answer'].split(',')
                for item in items:
                    if item == "":
                        continue
                    br,created = BinaryResource.objects.get_or_create(
                                        procedure=sp, element_id=k, guid=item)
                    br.total_size = 0
                    br.content_type = CONTENT_TYPES[v['type']]
                    if CONVERTED_CONTENT_TYPES.has_key(v['type']):
                        br.convert_before_upload = True
                        br.conversion_complete = False
                    br.save()
                    extension = BINARY_TYPES_EXTENSIONS[v['type']]
                    filename = '%s.%s' % (br.pk, extension)
                    br.data = br.data.field.generate_filename(br, filename)
                    path, file_ = os.path.split(br.data.path)
                    if not os.path.exists(path):
                        os.makedirs(path)
                    open(br.data.path, "w").close()
                    logging.info('BinaryResource -> %s has  file -> %s'
                                 % (br.pk, br.data.path))
                    br.save()
                    br = None
    except Exception,e:
        logging.error("Error creating BinaryResource stubs: %s" % str(e))
    return maybe_upload_procedure(sp)

def maybe_upload_procedure(saved_procedure):
    """Validates whether an encounter is ready to upload to the emr backend.
    Requires all associated BinaryResources be complete.

    Parameters:
        saved_procedure
            The SavedProcedure object which may be uploaded.
    """
    result = True
    message = ""
    logging.debug("Should I upload %s to the MRS?" % saved_procedure.guid)
    binaries = saved_procedure.binaryresource_set.all()

    ready = True
    waiting = []
    ready_list = []
    # checking all associated binaries
    for binary in binaries:
        if binary.ready_to_upload():
            message = ("Encounter: %s Binary: %s/%s COMPLETE" % (
                        saved_procedure.guid, binary.guid, len(binaries)))
            ready = ready and True
            ready_list.append(binary.guid)
        else:
            logging.debug("BinaryResource: %s completed: %s/%s" %
                         (binary.pk, binary.upload_progress, binary.total_size))
            waiting.append(binary.guid)
            message = ("Encounter: %s is WAITING on  %s"
                       % (saved_procedure.guid, waiting))
            ready = ready and False
    logging.debug("Encounter: %s has %s READY and %s WAITING"
                  % (saved_procedure.guid,ready_list,waiting))
    # We need to bail here if not ready
    if not ready:
        return result, message

    # if uploaded flag already true we don't want to try again
    if saved_procedure.uploaded:
        message = "Encounter -> %s, Already uploaded." %  saved_procedure.guid
        logging.info(message)
        return result, message

    # do the upload
    binaries_to_upload = [binary for binary in binaries if not binary.uploaded]
    logging.debug('Uploading Encounter -> %s, Binaries to upload = %s'
                  % (saved_procedure.guid, binaries_to_upload))
    files = defaultdict(list)

    # Set file for upload
    for binary in binaries_to_upload:
        files[str(binary.element_id)].append(str(binary.data.path))

    # prep text data for upload
    client_name = saved_procedure.client.name
    savedprocedure_guid = saved_procedure.guid

    # decodes and cleans up responses-OpenMRS specific
    responses = cjson.decode(saved_procedure.responses,True)
    cleaned_responses = []
    patient_id = ""
    patient_first = ""
    patient_last = ""
    patient_gender = ""
    patient_birthdate = ""
    patient_month = ""
    patient_day = ""
    patient_year = ""

    enrolled = 'Yes'
    enrolledtemp = responses.get('patientEnrolled', None)
    if enrolledtemp:
        enrolled = enrolledtemp.get('answer', 'Yes')
        del responses['patientEnrolled']

    procedure_title = ''
    procedure_title_element = responses.get('procedureTitle', None)
    if procedure_title_element:
        del responses['procedureTitle']
        procedure_title = procedure_title_element.get('answer', '')

    for eid,attr in responses.items():
        if enrolled == "Yes":
            if (eid == "patientId"):
                patient_id = attr.get('answer')
            elif (eid == "patientGender"):
                patient_gender = attr.get('answer')
            elif (eid == 'patientFirstName'):
                patient_first = attr.get('answer')
            elif (eid == 'patientLastName'):
                patient_last = attr.get('answer')
            elif (eid == 'patientBirthdateDay'):
                patient_day = attr.get('answer')
            elif (eid == 'patientBirthdateMonth'):
                patient_month = attr.get('answer')
            elif (eid == 'patientBirthdateYear') and (patient_year==""):
                patient_year = attr.get('answer')
            else:
                attr['id'] = eid
                cleaned_responses.append(attr)
        else:
            if (eid == "patientIdNew"):
                patient_id = attr.get('answer')
            elif (eid == "patientGenderNew"):
                patient_gender = attr.get('answer')
            elif (eid == 'patientFirstNameNew'):
                patient_first = attr.get('answer')
            elif (eid == 'patientLastNameNew'):
                patient_last = attr.get('answer')
            elif (eid == 'patientBirthdateDayNew'):
                patient_day = attr.get('answer')
            elif (eid == 'patientBirthdateMonthNew'):
                patient_month = attr.get('answer')
            elif (eid == 'patientBirthdateYearNew'):
                patient_year = attr.get('answer')
            else:
                attr['id'] = eid
                cleaned_responses.append(attr)
    patient_birthdate = '%s/%s/%s' % (months_dict[patient_month], patient_day,
                                      patient_year)

    if patient_id is None:
        patient_id = DEFAULT_PATIENT_ID

    if patient_gender in ['Male', 'male', 'M', 'm']:
        patient_gender = 'M'
    elif patient_gender in ['Female', 'female', 'F', 'f']:
        patient_gender = 'F'

    # Begin upload to the emr
    omrs = openmrs.OpenMRS(saved_procedure.upload_username,
                          saved_procedure.upload_password,
                          settings.OPENMRS_SERVER_URL)

    # creates the patient upstream if it does not exist
    new_patient = True if enrolled == "No" else False
    logging.debug("patient enrolled: %s" % new_patient)
    if new_patient:
        logging.debug("Creating new patient: patient_id -> %s" % patient_id)
    omrs.create_patient(patient_id,
                        patient_first,
                        patient_last,
                        patient_gender,
                        patient_birthdate)

    # execute upload
    logging.debug("Uploading to OpenMRS: %s %s %s %s %s "
                  % (patient_id, client_name,
                     savedprocedure_guid, files, cleaned_responses))
    result, msg, _ = omrs.upload_procedure(patient_id,
                                            client_name,
                                            procedure_title,
                                            savedprocedure_guid,
                                            cleaned_responses,
                                            files)
    message = 'sp.pk -> %s, %s ' % (saved_procedure.pk, msg)
    # mark encounter and binaries as uploaded
    logging.debug("API: RESULT = %s" % result )
    if result:
        saved_procedure.uploaded = True
        saved_procedure.save()
        for binary in binaries_to_upload:
            binary.uploaded = True
            binary.save()
            logging.debug("Uploaded = True %s" % binaries_to_upload)
        flush(saved_procedure)
    return result, message

def register_binary(procedure_guid, element_id, data):
    """Creates the BinaryResource object associated with an encounter.

    Parameters:
        procedure_guid
            The encounter id
        element_id
            The element within the encounter for which the binary was recorded
        data
            The request file field (data, name)
    """
    try:
        sp = SavedProcedure.objects.get(guid=procedure_guid)
    except SavedProcedure.DoesNotExist:
        logging.error("Couldn't register binary %s for %s -- the saved "
                      "procedure does not exist."
                      % (element_id, procedure_guid))
        return

    binary, _ = BinaryResource.objects.get_or_create(element_id=element_id,
                                                           procedure=sp)
    binary.data.save(data.name, data)
    binary.save()
    binary = None
    return maybe_upload_procedure(sp)

def register_binary_chunk(sp_guid, element_id, element_type, binary_guid,
                          file_size, byte_start, byte_end, byte_data):
    """Saves an iterable chunk of data to a BinaryResource file

    Parameters:
        sp_guid
            the encounter id
        element_id
            The element within the encounter for which the binary was recorded
        element_type
            The type attribute of the parent element
        binary_guid
            The comma separated value from the parent element answer attribute
            for this binary
        file_size
            The total size of the binary
        byte_start
            The offset from the start of the file for this chunk
        byte_end
            The byte_start + chunk size(deprecated)
        byte_data
            The chunk that will be written
    """
    logging.info("Registering binary chunk for: encounter -> %s, element_id -> %s)"
                 % (sp_guid, element_id))
    try:
        # Saved Procedure should have been created already
        sp = SavedProcedure.objects.get(guid=sp_guid)
        logging.info("Success opening SavedProcedure -> %d ." % sp.pk)
        binary, created = BinaryResource.objects.get_or_create(
                                                        element_id=element_id,
                                                        procedure=sp,
                                                        guid=binary_guid)
        logging.debug("Opened BinaryResource -> %d, new: %s" % (binary.pk,
                                                               created))
        # Have to include this here because thread switvhing under heavy load
        # will occasionally swap in register_saved_procedure before this happens
        # Shouldn't matter if client is operating correctly but we include to
        # be safe
        if created:
            filename = "%s.%s" % (binary.pk,
                                  BINARY_TYPES_EXTENSIONS[element_type])
            binary.create_stub(fname=filename)

        # if chunk was already received, i.e. receive_completed() = True, we may
        # be in one of two states:
        # 1. converting
        # 2. uploading
        # both may be caused by large file size
        if binary.receive_completed():
            if binary.convert_before_upload:
                if binary.conversion_complete:
                    message = "Uploading...."
                else:
                    message = "Converting..."
            else:
                message = "Uploading"
            return True, message
        binary.content_type = element_type
        binary.total_size = int(file_size)
        binary.save()

        # loop where we write the data to disk
        with open(binary.data.path, "r+b") as dest:
            bytes_written = 0
            offset = int(byte_start)
            byte_end = int(byte_end)
            dest.seek(0, os.SEEK_END)
            logging.info("upload_progress  = %s" % binary.upload_progress)
            if dest.tell() != int(offset):
                logging.error("WARNING: Synchronization: Client offset -> %s,"
                              "Server offset -> %s. Seeking to "
                              "appropriate location." % (dest.tell(), offset))
                dest.seek(offset, os.SEEK_SET)

            for chunk in byte_data:
                logging.info("writing %d bytes." % len(chunk))
                dest.write(chunk)
                bytes_written += len(chunk)
            dest.flush()
            # update BinaryResource  current position
            current_position = dest.tell()
            logging.debug("offset -> %s, upload_progress = %s"
                          % (current_position, binary.upload_progress))
            if current_position > binary.upload_progress:
                binary.upload_progress = current_position
            binary.save()
            logging.debug('Wrote binary chunk. File -> %s'% binary.data.path)
            logging.debug('chunk bytes -> %s, ' % bytes_written)
            logging.debug('binary upload progress -> %s of %s'
                     % (binary.upload_progress, binary.total_size))
        binary.save()

        # Check if upload is completed and convert
        if maybe_convert(binary):
            convert_binary(binary)
        binary = None
        result, message = maybe_upload_procedure(sp)

    except:
        etype, value, tb  = sys.exc_info()
        trace = traceback.extract_tb(tb)
        result = False
        message = ('SavedProcedure -> %s, BinaryResource -> %s: %s %s'
                   % (binary_guid, sp_guid, etype, value))

        for tbm in trace:
            logging.error(tbm)
    return result, message

def register_client_events(client_id, events):
    """Register one or more events for a client

    Parameters:
        client_id
            The client to register events for
        events
            The events to register
    """
    result = False
    result_message = "Could not process event log submission."

    client,_ = Client.objects.get_or_create(name=client_id)
    client.save()

    if hasattr(events, '__iter__'):
        count = 0

        for event in events:
            try:
                # Required
                event_type = event.get('event_type', None)
                event_value = event.get('event_value', None)
                event_time = event.get('event_time', None)

                # Should be milliseconds since epoch.
                event_time = int(event_time) / 1000.
                event_time = datetime.datetime.fromtimestamp(event_time)

                # Allow these as optional
                encounter_reference = event.get('encounter_reference', '')
                patient_reference = event.get('patient_reference', '')
                user_reference = event.get('user_reference', '')

                if event_type is None or event_value is None or event_time is None:
                    logging.error("Invalid event submission: %s" % event)
                    continue

                ClientEventLog(client=client,
                               event_type=event_type,
                               event_value=event_value,
                               event_time=event_time,
                               encounter_reference=encounter_reference,
                               patient_reference=patient_reference,
                               user_reference=user_reference).save()
                count += 1
            except Exception:
                etype, value ,_ = sys.exc_info()
                logging.error("%s %s" % (etype, value))
        result = True
        result_message = "Successfully saved %d events." % count

    return result, result_message

# transcoders should be in media.py
def maybe_convert(binary):
    """Returns True if the binary is a convertible type and the CONVERT_MEDIA
    flag is True in the settings.

    Parameters:
        binary
            The BinaryResource which will be checked for conversion
    """
    return (settings.CONVERT_MEDIA and binary.ready_to_convert())

def convert_binary(binary):
    """Executes conversion of the binary. Returns True if conversion is
    successful

    Parameters:
        binary
            The BinaryResource which will be checked for conversion
    """
    file_type = binary.content_type
    extension = CONVERTED_BINARY_TYPES_EXTENSIONS[file_type]
    type = CONVERTED_CONTENT_TYPES[file_type]
    logging.debug("CONVERSION ARGS: %s %s %s " % (binary, type, extension))
    result, message = FFmpeg().convert(binary, type, extension)
    logging.debug('FFmpeg: %s %s' % (result, message))
    return result
