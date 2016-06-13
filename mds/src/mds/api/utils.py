'''
Created on Feb 29, 2012


:Authors: Sana Dev Team
:Version: 1.2
'''
import logging
import os
import mimetypes
import uuid, random

import sys,traceback
from django.conf import settings

def make_uuid():
    """ A utility to generate universally unique ids.
    """
    return str(uuid.uuid4())

_mimemap = dict(settings.EXTENSIONS)

def guess_fext(mtype):
    """ A wrapper around mimetypes.guess_extension(type,True) with additional 
        types included from settings
        Parameters:
        mtype
            the file mime type
    """
    _tmp = mimetypes.guess_extension(mtype)
    return _mimemap.get(mtype,None) if not _tmp else _tmp

def key_generator(self):
    """ Generates a new secret key """
    return "".join([random.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)") for i in range(50)])

def printstack(e):
    """ Prints stack trace to console."""
    _, val, tb = sys.exc_info()
    trace = traceback.format_tb(tb)
    print 'Error: ', e
    print 'Value: ', val
    for tbm in trace:
        print tbm

def logstack(handler, e=None):
    logger = getattr(handler,'logger',logging)
    et, val, tb = sys.exc_info()
    trace = traceback.format_tb(tb)
    for tbm in trace:
        logger.error(unicode(tbm))
    return et, val, tb

def logtb(logger=None):
    if not logger:
        logger = logging
    et, val, tb = sys.exc_info()
    logger.info('Got an Error. Stack trace follows..')
    logger.error('...Exception type: %s' % repr(et))
    logger.error('...Exception value: %s' %repr(val))
    for tbm in traceback.format_tb(tb):
        logger.error(unicode(tbm))

def dictzip(keys,values):
    """ zips to lists into a dictionary """
    #if not keys or not values:
    #    raise Exception("Bad params")
    #if len(keys) != len(values):
    #    raise
    d = {}
    for x in list(zip(keys,values)):
        d[x[0]] = x[1]
    return d

def split(fin, path, chunksize=102400):
    """ Splits a file into a number of smaller chunks """
    print (fin, path, chunksize)
    if not os.path.exists(path):
        os.mkdir(path)
    partnum = 0
    input = open(fin, "rb")
    while True:
        chunk = input.read(chunksize)
        if not chunk: 
            break
        partnum += 1
        outfile = os.path.join(path,('chunk%s' % partnum))
        fobj = open(outfile, 'wb')
        fobj.write(chunk)
        fobj.close()
    input.close()
    return partnum

def exception_value(ex=None):
    return repr(ex) if ex else sys.exc_info()[1]
    
def related_namegen(app,klass):
    return  "%{app}_%{klass}s_related".format(app=app.lower(), 
                                              klass=klass.lower())
