from piston.doc import generate_doc
from .handlers import *


session_doc = generate_doc(SessionHandler)
concept_doc = generate_doc(ConceptHandler)
encounter_doc = generate_doc(EncounterHandler)
obs_doc = generate_doc(ObservationHandler)
procedure_doc = generate_doc(ProcedureHandler)
subj_doc = generate_doc(SubjectHandler)
