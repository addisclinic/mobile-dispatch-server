""" An entity about whom data is collected.

:Authors: Sana dev team
:Version: 2.0
"""
import datetime
import os
from PIL import Image
from django.db import models
from mds.api.utils import make_uuid

__all__ = ["AbstractSubject","Subject","SurgicalSubject"]

class AbstractSubject(models.Model):
    """ The entity about whom data is collected. """
    class Meta:
        abstract = True
    
    uuid = models.SlugField(max_length=36, unique=True, default=make_uuid, editable=False)
    """ A universally unique identifier """
    
    created = models.DateTimeField(auto_now_add=True)
    """ When the object was created """
    
    modified = models.DateTimeField(auto_now=True)
    """ updated on modification """
    
    voided = models.BooleanField(default=False)

class Subject(AbstractSubject): 
    """ Simple subject implementation as a medical patient. 
    """
    class Meta:
        app_label = "core"
    given_name = models.CharField(max_length=64)

    family_name = models.CharField(max_length=64)

    dob = models.DateTimeField()

    gender = models.CharField(choices=(("M","M"),("F","F")),max_length=2)

    image = models.ImageField(blank=True, upload_to="core/subject")

    location = models.ForeignKey('Location', blank=True, to_field='uuid')

    system_id = models.CharField(max_length=64, blank=True)

    @property
    def age(self):
        """ Convenience wrapper to calculate the age. """
        today = datetime.date.today()
        if self.dob > datetime.date.today().replace(year=self.dob.year):
            return today.year -self.dob.year - 1
        else:
            return today.year -self.dob.year

    @property
    def full_name(self):
        return u'%s, %s' % (self.family_name,self.given_name)

    def _generate_thumb(self, size=(96,96)):
        try:
            pth, fname = os.path.split(self.image.path)
            thumb_pth = os.path.join(pth, "ico")
            thumb = os.path.join(thumb_pth,fname)
            if not os.path.exists(thumb_pth):
                os.makedirs(thumb_pth)
            im = Image.open(self.image.path)
            thim = im.copy()
            thim.thumbnail(size, Image.ANTIALIAS)
            thim.save(thumb)
        except:
            pass

    @property
    def thumb_url(self):
        try:
            pth, fname = os.path.split(self.image.path)
            thumb_pth = os.path.join(pth, "ico")
            thumb = os.path.join(thumb_pth,fname)
            if not os.path.exists(thumb):
                self._generate_thumb()
            url_path, _  = os.path.split(self.image.url)
            thumb_url_path = os.path.join(url_path, "ico") 
            return os.path.join(thumb_url_path, fname)
        except:
            return self.image.url

    def save(self, *args, **kwargs):
        super(Subject, self).save(*args, **kwargs)
        self._generate_thumb()

    def __unicode__(self):
        return u'%s, %s - %s' % (self.family_name, self.given_name, self.system_id)
