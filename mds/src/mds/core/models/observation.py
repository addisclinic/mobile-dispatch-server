""" An instance of data collection corresponding to a single step within a 
Procedure.

:Authors: Sana dev team
:Version: 2.0
"""
import mimetypes, os

from django.db import models
from django.utils.translation import ugettext as _

from mds.api.utils import make_uuid, guess_fext

_app = "core"

class Observation(models.Model):
    """ A piece of data collected about a subject during an external_id"""

    class Meta:
        app_label = "core"  
        unique_together = (('encounter', 'node'),)
        ordering = ["-created"]

    def __unicode__(self):
        return "%s %s" % ( 
            self.concept.name,
            unicode(self.value), 
    )
    uuid = models.SlugField(max_length=36, unique=True, default=make_uuid, editable=False)
    """ A universally unique identifier """
    
    encounter = models.ForeignKey('Encounter', to_field='uuid')
    """ The instance of a procedure which this observation is associated with. """
    
    node = models.CharField(max_length=255)
    '''Unique node id within the external_id as defined by the original procedure.'''

    concept = models.ForeignKey('Concept', to_field='uuid')
    """ A dictionary entry which defines the type of information stored.""" 
    
    value_text = models.CharField(max_length=255)
    """ A textual representation of the observation data.  For observations
        which collect file data this will be the value of the absolute
        url to the file
    """
    
    value_complex = models.FileField(upload_to='{0}/observation'.format(_app), blank=True,)
    """ File object holder """
    
    # next two are necessary purely for packetizing
    _complex_size = models.IntegerField(default=0)
    """ Size of complex data in bytes """
    
    _complex_progress = models.IntegerField(default=0)
    """ Bytes recieved for value_complex when packetized """
    
    created = models.DateTimeField(auto_now_add=True)
    """ When the object was created """
    
    modified = models.DateTimeField(auto_now=True)
    """ updated on modification """
    
    voided = models.BooleanField(default=False)
    
    @property
    def subject(self):
        """ Convenience wrapper around Encounter.subject """
        if self.encounter:
            subj = self.encounter.subject
        else:
            subj = None
        return subj
    
    @property
    def is_complex(self):
        """ Convenience wrapper around Concept.is_complex """
        if self.concept:
            return self.concept.is_complex
        else:
            False
    
    @property
    def data_type(self):
        """ Convenience wrapper around Concept.data_type """
        if self.concept:
            return self.concept.datatype
        else:
            return None
    
    @property
    def device(self):
        """ Convenience wrapper around Encounter.device """
        if self.encounter and self.encounter.device:
            return self.encounter.device.name
        else:
            return None
    
    @property
    def question(self):
        """ Convenience property for matching the object to the procedure
            instruction-i.e. the question on a form.
        """
        return self.node
    
    def open(self, mode="w"):
        if not self.is_complex:
            raise Exception("Attempt to open file for non complex observation")
        path, _ = os.path.split(self.value_complex.path)
        # make sure we have the directory structure
        if not os.path.exists(path):
            self.create_file()
        return open(self.value_complex.path, mode)
    
    def _generate_filename(self):
        name = '%s-%s' % (self.encounter.uuid, self.node)
        ext = guess_fext(self.concept.mimetype)
        fname = '%s.%s' % (name, ext)
        
        
    def create_file(self, append=None):
        """ Creates a zero length file stub on disk
            Parameters:
            append
                Extra string to append to file name.
        """
        name = '%s-%s' % (self.encounter.uuid, self.node)
        if append:
            name += '-%s' % append
        ext = guess_fext(self.concept.mimetype)
        fname = '%s%s' % (name, ext)
        self.value_complex = self.value_complex.field.generate_filename(self, fname)
        path, _ = os.path.split(self.value_complex.path)
        # make sure we have the directory structure
        if not os.path.exists(path):
            os.makedirs(path)
            # create the stub and commit if no exceptions
            open(self.value_complex.path, "w").close()
        self.save()
    
    @property
    def complete(self):
        if self._complex_size is 0:
            return True
        else:
            return not self._complex_progress < self._complex_size
            
    @property
    def value(self):
        if self.is_complex:
            return self.value_complex
        else:
            return self.value_text

    @property
    def upload_progress(self):
        if self.is_complex:
            return "%d/%d" % (self._complex_progress, self._complex_size)
        else:
            return u"NA"

    def encounter_uuid(self):
        return self.encounter.uuid
        
    def save(self,*args,**kwargs):
        if self.is_complex:
            self.value_text = _('complex data')
        super(Observation,self).save(*args, **kwargs)
