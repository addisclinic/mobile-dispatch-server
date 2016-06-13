
from piston.resource import Resource
from .handlers import *

__all__ = [
    'rsrc_concept',
    'rsrc_relationship', 
    'rsrc_relationshipcategory', 
    'rsrc_device',
    'rsrc_location',
    'rsrc_subject',
    'rsrc_observer',
    'rsrc_procedure',
    'rsrc_encounter',
    'rsrc_observation',
    'rsrc_notification',
    'rsrc_event',
    'rsrc_doc',
    'rsrc_session',
]

rsrc_concept = Resource(ConceptHandler)
rsrc_relationship = Resource(RelationshipHandler)
rsrc_relationshipcategory = Resource(RelationshipCategoryHandler)
rsrc_device = Resource(DeviceHandler)
rsrc_location = Resource(LocationHandler)
rsrc_subject = Resource(SubjectHandler)
rsrc_observer = Resource(ObserverHandler)
rsrc_procedure = Resource(ProcedureHandler)

rsrc_encounter = Resource(EncounterHandler)
rsrc_observation = Resource(ObservationHandler)

rsrc_notification = Resource(NotificationHandler) 
rsrc_event = Resource(EventHandler)

rsrc_doc = Resource(DocHandler)
rsrc_session = Resource(SessionHandler)
