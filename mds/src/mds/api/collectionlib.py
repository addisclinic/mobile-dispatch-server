'''
Data access objects for representing complex structures.

Created on Nov 30, 2011

:Authors: Sana Dev Team
:Version: 1.1
'''
import os
import mimetypes
import logging
from django.core.files import File

from .utils import guess_fext
from mds.core.models import Observation, Concept

__all__ = ['ObservationSet']

class Set(object):
    """ Dictionary backed set class
    """
    def __init__(self, value=[]):
        self.data = {}
        self.concat(value)
        
    def intersect(self, other):
        res = {}
        for x in other:
            if x in self.data:
                res[x] = None
        return Set(res.keys())
    
    def union(self, other):
        res = {}
        for x in other:
            res[x] = None
        for x in self.data.keys():
            res[x] = None
        return Set(res.keys())
    
    def concat(self, value):
        for x in value:
            self.data[x] = None

    def __len__(self): 
        return len(self.data)
    
    def __getitem__(self,key):
        return self.data[key]
    
    def __and__(self,other):
        return self.intersect(other)
    
    def __or__(self,other):
        return self.union(other)
    
    def __repr__(self):
        return '<Set: ' + repr(self.data) + '>'
    
class ObservationSet(Set):
    
    def __init__(self, encounter, value=[]):
        super(ObservationSet,self).__init__(value=value)
        self.encounter = encounter
        
    def create_all(self, obs_data={}, files=[], id_as_key=False):
        """ Creates a set of observations from a dict of data
        
            Parameters:
                obs_data
                    a dictionary of observations
                files
                    a list of UploadedFile objects
                id_as_key
                    legacy bit for setting the node name equal to the dict key
        """
        complete = True
        for k,v in obs_data.items():
            _obs = {}
            logging.debug('Creating observation, %s {"%s":%s}'% (type(v).__name__,k,v))
            _obs['encounter'] = self.encounter
            _obs['node']= k
            _obs['value'] = v['value']
            # Changed this to allow creation
            _cdata = { "name" : v['concept']}
            if v['concept'].upper().find('PICTURE') > -1:
                _cdata["is_complex"] = True
                _cdata["data_type"]  = "image/jpg"
            logging.debug("Concept: %s" % _cdata)
            concept,_ = Concept.objects.get_or_create(**_cdata)
            
            _obs['concept'] = concept
            item_complete = True
            if concept.is_complex:
                item_complete = False 
                items = _obs['value'].split(',')
                for item in items:
                    if item == "":
                        continue
                    
                    _obs['node'] = '%s-%s' % (k, item)
                    obs,_ = Observation.objects.get_or_create(**_obs)
                    
                    # build out file
                    ext = guess_fext(concept.data_type)
                    fpfx = '%s-%s' % (self.encounter.uuid, _obs['node'])
                    fname = '%s.%s' % (fpfx, ext)
                    obs.value_complex = obs.value_complex.field.generate_filename(obs, fname)
                    path, _ = os.path.split(obs.value_complex.path)
                    if not os.path.exists(path):
                        os.makedirs(path)
                    open(obs.value_complex.path, "w").close()
                    obs.save()
                        
                    _file = files.get(obs.node,None)
                    if _file:
                        self.write(obs, _file)
                        item_complete = True
                        obs.uploaded = True
                        obs.save()
                    #self._data.add(obs.node, obs) 
            else:
                obs,_ = Observation.objects.get_or_create(**_obs)
                #self._data.add(obs.node, obs)
                complete = complete and item_complete
        self.encounter.uploaded = complete
        self.encounter.save()
        
    def write_value_complex(self,obs, file):
        
        path, _ = os.path.split(obs.value_complex.path)
        if not os.path.exists(path):
            os.makedirs(path)
        obs._complex_size = file.size
        
        destination = open(obs.value_complex.path, 'wb+')
        bytes_written = 0
        for chunk in file.chunks():
            destination.write(chunk)
            bytes_written += chunk.size
        obs._complex_progess = bytes_written
        obs.save()
        
    
