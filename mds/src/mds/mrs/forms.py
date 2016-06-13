"""
Form definitions for 1.x versions of mDS.

:Authors: Sana dev team
:Version: 1.2
"""
from django import forms

class PacketForm(forms.Form):
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
    done = forms.BooleanField(initial=False, required=False)

class BinaryPacketForm(PacketForm):
    """Packet form for binary data """
    byte_data = forms.FileField()
    
class Base64PacketForm(PacketForm):
    """Packet form for binary data encoded as base64 text. """
    byte_data = forms.CharField()
    
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
    subject = forms.CharField(required=False)
    phone = forms.CharField(max_length=255, required=False, initial='')

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

