''' 
Mapping objects for translating between MDS data model and OpenMRS
representations.

The MDS data model is significantly simpler and hence there is 
not a one-to-one mapping between the two. Below is the full list of
OpenMRS objects available through the REST API

ActiveListType
Cohort
CohortMember
Concept
ConceptClass
ConceptDatatype
ConceptDescription
ConceptMap
ConceptMapType
ConceptName
ConceptReferenceTerm
ConceptReferenceTermMap
ConceptSource
Drug
Encounter
EncounterType
Field
FieldAnswer
FieldType
Form
FormField
HL7
HL7Source
Location
LocationAttribute
LocationAttributeType
LocationTag
Obs
Order
DrugOrder subclass of Order
OrderType
Patient
PatientIdentifier
PatientIdentifierType
Person
PersonAddress
PersonAttribute
PersonAttributeType
PersonName
Privilege
Problem
Provider
ProviderAttribute
ProviderAttributeType
Role
User
Visit
VisitAttribute
VisitAttributeType
VisitType

Source: https://wiki.openmrs.org/display/docs/REST+Web+Service+Resources+in+OpenMRS+1.9
'''
import datetime
import cjson

from django.conf import settings
from django.contrib.auth.models import User

from mds.api.contrib.backends.models import *
from mds.core.models import *

__all__ = [
    'm_encounter',
    'm_name',
    'm_observer',
    'm_person',
    'm_subject',
    'm_user',
    'EncounterTransform',
    'PersonNameTransform',
    'PersonTransform',
    'SubjectTransform',
    'UserTransform',
]

class OpenMRSModelTransform(ModelTransform):
    def read(self,instance):
        if isinstance(instance, list):
            return [self.decode(x) for x in instance]
        else:
            return self.decode(instance)

class PersonNameTransform(TransformBase):
    ''' Sana data model does not include a discrete PersonName model.
        This class performs a dictionary to dictionary mapping.
        Naming conventions for local representation follow MDS
        Model classes
        
        OpenMRS fields
        uuid
        givenName
        familyName
        
    '''

    def decode(self,instance):
        data = {}
        data['given_name'] = instance['givenName']
        data['family_name'] = instance['familyName']
        return data

    def encode(self, instance):
        data = {}
        data['givenName'] = get_field_value('given_name', instance)
        data['familyName'] = get_field_value('family_name', instance)
        return data
        
m_name = PersonNameTransform()

class PersonTransform(TransformBase):
    ''' Sana data model does not include a discrete Person model.
        This class performs a dictionary to dictionary mapping.
        Naming conventions for local representation follow Sana
        Model classes.
        
        Full OpenMRS representation includes
        
        uuid
        gender
        birthdate
        preferredName(decode)
        names(encode)
    '''
    
    def decode(self,instance):
        data = {}
        data['uuid'] = instance['uuid']
        name = m_name.decode('preferredName')
        data['given_name'] = name.get('given_name')
        data['family_name'] = name.get('family_name')
        return data
        
    def encode(self, instance):
        ''' Encode into person representation.instance must have
            'given_name', 'family_name', 'dob', and 'gender' attrs
        '''
        data = {}
        name = {}
        name['givenName'] = get_field_value('given_name',instance)
        name['familyName'] = get_field_value('family_name',instance)
        data['names'] = [name]
        data['gender'] = get_field_value('gender',instance)
        dob = get_field_value('dob', instance)
        data['birthdate'] = dob.isoformat()
        return data

m_person = PersonTransform()

class SubjectTransform(ModelTransform):
    ''' Implementation of fairly generic Sana Subject model
        to the OpenMRS Patient
    '''
    def __init__(self):
        super(SubjectTransform,self).__init__(Subject)

    def decode(self, instance):
        result = Subject()
        result.uuid = instance["uuid"]
        person = instance['person']
        # Hacked way of doing this
        # We can parse the id and name from 'display'
        display =  instance.get('display', "NULLID - NULL NAME")
        system_id, name = display.split('-')
        result.system_id = system_id.strip()
        # have to split and strip name as well
        given_name, family_name = name.strip().split(' ')
        result.given_name = given_name.strip()
        result.family_name = family_name.strip()
        try:
            # Note the REST API does not return these on a POST
            identifier = instance['identifiers'][0]
            result.dob = person["birthdate"]
            name = person.get("preferredName")
            result.system_id = identifier.get('identifier',None)
            result.given_name = name["givenName"]
            result.family_name = name["familyName"]
            result.gender = person["gender"]
        except:
            pass
        return result

    def encode(self, instance):
        ''' Encode to OpenMRS patient representation
        
            Requires
                person
                identifiers
        '''
        # construct person
        person = {}
        name = {}
        name['givenName'] = get_field_value('given_name',instance)
        name['familyName'] = get_field_value('family_name',instance)
        person['names'] = [name]
        person['gender'] = get_field_value('gender',instance)
        dob = get_field_value('dob', instance)
        person['birthdate'] = dob.isoformat()
        # Identifiers
        identifiers = [ {
            "identifier": instance.system_id,
            "identifierType": {
                'uuid': "8d79403a-c2cc-11de-8d13-0010c6dffd0f"
            },
            "location": {
                        "uuid": "8d6c993e-c2cc-11de-8d13-0010c6dffd0f"
            }
            }]
        # Construct the OpenMRS representation
        data = {}
        data ['person'] = person
        data['identifiers'] = identifiers
        return data
        
m_subject = SubjectTransform()

class EncounterTransform(ModelTransform):

    def __init__(self):
        super(EncounterTransform,self).__init__(Encounter)
    
    def read(self, instance):
        pass
        
    def write(self, instance):
        pass
m_encounter = EncounterTransform()

class UserTransform(TransformBase):
    ''' Observer to User transform. The Sana client assumes all
        app users are effectively observers
        
        OpenMRS user object
            uuid
            username
            systemId*
            person
            privileges*
            roles*
    '''
    def decode(self, instance):
        ''' Decodes user.username and uuid from OpenMRS object.
        '''
        obj = {}
        obj['uuid'] = instance.get('uuid')
        username = instance.get('username', None)
        # fall back in case username is not set
        if not username:
            username = instance.get('systemId')
        obj['user'] = { 'username': username }
        return obj
m_user = UserTransform()

class ObserverTransform(ModelTransform):

    def __init__(self):
        super(ObserverTransform,self).__init__(Observer)

    def decode(self, instance):
        obj = Observer()
        obj.uuid = instance.get('uuid')
        username = instance.get('username', None)
        user = User(username=username)
        obj.user = user
        return obj
m_observer = ObserverTransform()
