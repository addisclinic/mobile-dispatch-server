# Create your models here.
import mimetypes, os

from django.db import models


class Client(models.Model):

    version = models.CharField(max_length=255)
                                
    app = models.FileField(upload_to='clients/', blank=True,)
