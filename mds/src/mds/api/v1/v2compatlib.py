""" Utilities for transforming from the 1.x to other versions.

:Authors: Sana dev team
:Version: 1.1
"""
import logging
from uuid import UUID
import re
import cjson as _json
import shutil, os

from django.contrib.auth.models import User, UserManager

from django.views.generic import RedirectView
#from django.views.generic import redirect_to
from xml.etree import ElementTree
from xml.etree.ElementTree import parse

from mds.core import models as v2

_deprecated = ('patientEnrolled',
              "patientId",
              "patientGender",
              'patientFirstName',
              'patientLastName',
              'patientBirthdateDay',
              'patientBirthdateMonth',
              'patientBirthdateYear',
              "patientIdNew",
              "patientGenderNew",
              'patientFirstNameNew',
              'patientLastNameNew',
              'patientBirthdateDayNew',
              'patientBirthdateMonthNew',
              'patientBirthdateYearNew',)
""" Deprecated terms not used within observations """


LCOMPLEX_TYPES = { 'PICTURE': 'image/jpeg',
                   'SOUND': 'audio/3gpp',
                   'VIDEO': 'video/3gpp',
                   'BINARYFILE': 'application/octet-stream'}

def redirect_to_v1(request, url, query_string=True, **kwargs):
    return redirect_to(request, url, query_string=query_string, **kwargs)

class V1RedirectView(RedirectView):
    query_string = True
    

def strip_deprecated_observations(observations):
    """ Removes old bio glomming in the observation dict 
        Parameters:
        observations
            A dictionary of observations.
    """
    _obs = {}
    #_obs = dict([(lambda x: (k,v) for k not in deprecated)(observations)])
    for k,v in observations.items():
        if k not in _deprecated:
            _obs[k] = v 
    return _obs

def element2obs(obs, allow_null=False):    
    """ Remaps the old format to new api Observation model for a single
        observation. Returns a dictionary, not an observation instance.
    """
    # Should only be one
    _obs = {}
    #For now we require non-empty strings
    if obs['answer']:
        _obs['value'] = obs['answer']
    else:        
        return {}
    node = obs.keys()[0]
    _obs['node'] = node
    _obs['concept'] = obs['concept']
    return _obs


def elements2obs(observations, allow_null=False):
    """ Remaps the old format to new api Observation model. Returns only the 
        text dictionary, not the actual observations.
    """
    _obs_set = {}
    for k,v in observations.items():
        _obs = {}
        #For now we require non-empty strings
        if v['answer']:
            _obs['value'] = v['answer']
        else:
            continue
        _obs['node'] = k
        _obs['concept'] = v['concept']
        logging.debug('Obs: %s' % _obs)
        _obs_set[k] = _obs
    return _obs_set

# TODO
def bchunk2bpacket(form):
    """ Converts the old binary chunk packet form into the v2 api
    """
    encounter = form.cleaned_data['procedure_guid']
    node = form.cleaned_data['element_id']
    subnode = form.cleaned_data['binary_guid']
    node = '%s-%s'% (node, subnode)
    type = form.cleaned_data['element_type']
    size = form.cleaned_data['file_size']
    offset = form.cleaned_data['byte_start']
    byte_end = form.cleaned_data['byte_end']
    return {}

class LProcedureParsable:
    """ A new parsed legacy procedure backed by an ElementTree.
        The default behavior of the constructor is to use the 
        text parameter as the xml if both text and xml are not None 
        
            Parameters
                text
                    An xml string
                path
                    The path to a file containing the xml to parse
        """
    def __init__(self, text=None, path=None ):
        self.root = None
        self._parse(text=text, path=path)
        
    def _parse(self, text=None, path=None):
        if text:
            self.root = ElementTree.XML(text)
        elif path: 
            self.root = parse(path).getroot()
        
    def __call__(self,text=None, path=None):
        self._parse(text=text, path=path)
    
    @property
    def concepts(self):
        def _map(x):
            mime = LCOMPLEX_TYPES.get(x.attrib['type'], 'text/plain')
            return { 'name' : x.attrib['concept'], 
                     'description' : x.attrib['question'],
                     'is_complex' : (mime != 'text/plain'),
                     'data_type' : mime }
        return list(_map(x) for x in self.root.findall('Page/Element'))
    
    @property
    def pages(self):
        return list(x for x in self.root.findall('Page'))
    
    @property
    def elements(self):
        return list(x.attrib for x in self.root.findall('Page/Element'))
        
    def to_python(self):
        ''' Converts the parsed object to a dict '''
        _p = {}
        self._rdict(_p, self.root)
        return _p
    
    def _rdict(self, pdict, node, indent=0):
        """ Recursive helper method for building the python object """
        # append all of the children as 'tag': dict([*node.attrs, dict(children)
        _current = node.attrib
        for n in list(node):
            _a = {}
            self._append(_current, n, indent+4)
            if n.tag in _current:
                list(_current[n.tag]).append(_a)
            else:
                _current[n.tag] = _a
        pdict[node.tag] = _current
    
lpp = LProcedureParsable

def responses_to_observations(encounter, responses,sort=False,reverse=False):
    observations = []
    logging.info("Converting %d observations" % len(responses))
    # Begin loop over observations
    for node,data in responses.items():
        obs = None
        concept_name = data.get('concept', None)
        logging.info("" + node + ":"+concept_name)
        if not concept_name:
            logging.debug("No concept_name")
            continue
        try:
            concept = v2.Concept.objects.get(name=concept_name)
        except:
            logging.error("Unable to find concept with name: %s" % concept_name)
            continue
                
        answer = data['answer']
        uuid = data['uuid']
        if concept and concept.is_complex:
            logging.info("Got complex concept: node: %s, answer: %s" % (node,answer))
            if not answer or answer == "":
                continue
            answer, _, additional = answer.partition(',')
            # Begin Complex obs loop
            while True:
                value_text = "complex data"
                try:
                    obs = v2.Observation.objects.get(
                          uuid=uuid)
                    obs.encounter=encounter
                    obs.node=node
                    obs.concept=concept
                    obs.value_text=value_text
                    obs.save()
                    logging.debug("Updated complex observation: %s" % obs.uuid)
                except:
                    logging.info("Creating new complex obs for encounter: %s" % encounter.uuid)
                    obs = v2.Observation.objects.create(
                          uuid=data['uuid'],
                          encounter=encounter,
                          node=node,
                          concept=concept,
                          value_text=answer)
                    obs.save()
                    logging.debug("Created complex observation: %s" % obs.uuid)
                observations.append(obs)
                answer, _, additional = answer.partition(',') if answer else None
                if not additional:
                    break
                # End complex obs loop
        else:
            answer = answer if answer else 'no response'
            try:
                obs = v2.Observation.objects.get(
                          uuid=uuid)
                obs.encounter=encounter
                obs.node=node
                obs.concept=concept
                obs.value_text = answer
                obs.save()
                logging.debug("Updated observation: %s" % obs.uuid)
            except:
                logging.info("Creating new obs for encounter: %s" % encounter.uuid)
                obs = v2.Observation.objects.create(
                          uuid=uuid,
                          encounter=encounter,
                          node=node,
                          concept=concept,
                          value_text=answer)
                obs.save()
                logging.debug("Created observation: %s" % obs.uuid)
            observations.append(obs)
            # END LOOP    
    if sort:
        sorted_observations = sort_by_node(observations)
        logging.info("Return %d sorted observations" % len(sorted_observations))
        for x in sorted_observations:
            x.save()
        observations = sorted_observations
    return observations

def sort_by_node(observations,descending=True):
    npaths = []
    for x in observations:
        ids = x.node.split("_")
        if len(ids) == 1:
            if x.node.isdigit():
                npaths.append((x, int(x.node), 0))
            else:
                npaths.append((x, int(x.node[:-1]), x.node[-1:]))
        else:
            npaths.append((x,int(ids[0]),int(ids[1])))
    npaths_sorted = sorted(npaths,key=lambda pth: pth[2], reverse=descending)
    node_tuples = sorted(npaths_sorted,key=lambda pth: pth[1],reverse=descending)
    sorted_observations = [x[0] for x in node_tuples]
    return sorted_observations
    #sorted_keys = ["%d%s" % (x[1],x[2] if x[2] else str(x[0]) for x in node_tuples ]
    #max_length = 0
    #for node in nodes:
    #    max_length = max(len(x),max_length)
    #sorted_ids = None
    #return None

_regex = re.compile('^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}\Z', re.I)

def validate_uuid(v):
    try:
        UUID(v)
        return True
    except:
        return False
    return True

def get_v2(klazz,v,field):
    obj = None
    if validate_uuid(v):
        obj = klazz.objects.get(uuid=v)
    else:
        obj = klazz.objects.get(**{ field : v })
    return obj

def get_or_create_v2(klazz,v,field, data={}):
    obj = None
    if validate_uuid(v):
        # Assume a get call if we pass the uuid
        obj = klazz.objects.get(uuid=v)
    else:
        data[field] = v
        q = { field: v}
        qs = klazz.objects.filter(**q)
        if len(qs) >= 1:
            obj = qs[0]
        else:
            obj,_  = klazz.objects.get_or_create(**data)
    return obj


def spform_to_encounter(form):
    savedproc_guid  = form['savedproc_guid']
    procedure_guid = form['procedure_guid']
    responses = form['responses']
    phone = form['phone']
    username = form['username']
    password = form['password']
    patientId = form['subject']

    procedure = get_v2(v2.Procedure,procedure_guid,"title")
    # check if they are an SA in which case we have a device
    # otherwise we fall back to the old behavior
    try:
        observer = get_v2(v2.SurgicalAdvocate, username, "user__username")
    except:
        observer = get_v2(v2.Observer, username, "user__username")
    # if SA use the assigned device otherwise fall back to the old
    # behavior
    try:
        if isinstance(observer,v2.SurgicalAdvocate):
            device = observer.device
        else:
            device = get_or_create_v2(v2.Device, phone, "name")
    except:
        device = get_or_create_v2(v2.Device, phone, "name")

    subject = get_v2(v2.Subject, patientId, "system_id")
    concept = get_v2(v2.Concept,"ENCOUNTER","name")
    created = True
    try:
        encounter = v2.Encounter.objects.get(uuid=savedproc_guid)
        created = False
    except:
        encounter = v2.Encounter(
            uuid=savedproc_guid,
            procedure=procedure,
            observer=observer,
            device=device,
            subject=subject,
            concept=concept)
        encounter.save()
    '''
    encounter,created = v2.Encounter.objects.get_or_create(uuid=savedproc_guid,
		    procedure=procedure,
		    observer=observer,
		    device=device,
		    subject=subject,
		    concept=concept)
    '''
    data = strip_deprecated_observations(_json.decode(responses))
    return encounter, data,created
                                                            
def sp_to_encounter(sp, subject):
    procedure = get_v2(v2.Procedure, sp.procedure_guid,"title")
    observer = get_v2(v2.Observer, sp.upload_username, "user__username")
    device = get_v2(v2.Device, sp.client.name,"name")
    #subject = get_v2(Subject, patientId, "system_id")
    concept = get_v2(v2.Concept,"ENCOUNTER","name")
    
    
    encounter,created = v2.Encounter.objects.get_or_create(
		    uuid=sp.guid,
		    procedure=procedure,
		    observer=observer,
		    device=device,
		    subject=subject,
		    concept=concept)
    data = strip_deprecated_observations(_json.decode(sp.responses))
    return encounter, data, created
    
def write_complex_data(br):
    #encounter = v2.Encounter.objects.get(uuid=br.procedure.guid)
    obs = v2.Observation.objects.get(encounter=br.procedure.guid,
				     node=br.element_id)
    if not obs.concept.is_complex:
	return
    #obs.value_complex = obs.value_complex.field.generate_filename(obs, fname)
    path, _ = os.path.split(obs.value_complex.path)
    if not os.path.exists(path):
        os.makedirs(path)
    open(obs.value_complex.path,"w").close()
    obs._complex_size = br.total_size
    obs.save()
    # make sure we have the directory structure
    #pathIn = "%s%s" % (settings.MEDIA_ROOT ,br.data.name)
    #pathOut = "%s%s" % (settings.MEDIA_ROOT, obs.value_complex.name)
    #if not os.path.exists(path):
    #    os.makedirs(path)
    os.rename(br.data.path,obs.value_complex.path)

    # Successfully renamed so we update the progress
    obs._complex_progress = br.upload_progress
    obs.save()
    #shutil.copyfile(pathIn,pathOut)


def render_response_v1(response, version=2):
    """ Renders a response into version 1 compatible format
    
        response:
            a dict to convert
        version:
            the version of the response
    """
    if version == 2:
        status = response.get("status")
        data = response.get("message")
        return {"status": status,
                "data" : data }
    else:
        return response

if __name__ == '__main__':
    """ Run this as 
            python legacy_utils.py procedure $FILE
        to print a procedure to stdout
    """
    import sys
    if sys.argv[1] == 'p':
        _ptext = sys.argv[3]
        _pr = lpp(path=_ptext)
        if sys.argv[2] == 'p':
            print ' '*4,_pr.root.attrib
        elif sys.argv[2] == 'e':
            for e in _pr.elements:
                print ' '*4, e
        elif sys.argv[2] == 'c':
            for c in _pr.concepts:
                print c
    
