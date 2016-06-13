"""Provides utilities for converting media types. 

Additional media converters should be added as callables which return True upon 
successful transcoding.

:Authors: Sana dev team
:Version: 1.1
"""
#TODO The above really should have used __call__ 
from __future__ import with_statement

from mds.api.encoders.ffmpeg import FFmpeg

BINARY_TYPES = ['PICTURE', 'SOUND', 'VIDEO', 'BINARYFILE']
"""Element types that may include file data."""

BINARY_TYPES_EXTENSIONS = {
    'PICTURE': 'jpg',
    'SOUND': '3gp',
    'VIDEO': '3gp',
    'BINARYFILE': 'mpg',}
"""File extensions for the binary types.""" 

CONTENT_TYPES = {
    'PICTURE': 'image/jpeg',
    'SOUND': 'audio/3gpp',
    'VIDEO': 'video/3gpp',
    'BINARYFILE': 'video/mpeg'}
"""Mime types for client content."""
#'BINARYFILE': 'application/octet-stream'}

CONVERTED_BINARY_TYPES_EXTENSIONS = {
    'SOUND': 'mp3',
    'VIDEO': 'flv',}
"""File extensions for transcoded files."""

CONVERTED_CONTENT_TYPES = {
    'SOUND': 'audio/mpeg',
    'VIDEO': 'video/x-flv'}
"""Mime types of files that will be uploaded."""


# Target types and extensions
TYPES = {'SOUND': 'audio/mpeg',
         'VIDEO': 'video/x-flv'}
"""Transcoded taget types"""

# File extensions for converted types
EXTENSIONS = {'SOUND': 'mp3',
              'VIDEO': 'flv'}
"""Transcoded file extensions"""

# Converter objects
_ffmpeg = FFmpeg()

# Type to converter dictionary
CONVERTERS = { 'SOUND': _ffmpeg,
               'VIDEO': _ffmpeg}
"""Type to transcoder mapping"""

# Utility methods for this module 
def is_convertible(content_type):
    """Returns True if media content type is convertible 
     
     Parameters:
         content_type
             the type of content to check for needed conversion
    """
    return TYPES.has_key(content_type)

def get_extension(content_type):
    """Returns file extension
     
     Parameters:
        content_type
            the type of content to get an extension for
    """
    return EXTENSIONS[content_type]

def get_converter(content_type):
    """Returns converter object. All converter objects should have convert 
    method.
    
    Parameters:    
        content_type
            the type of content to check for a converter
    """
    return CONVERTERS[content_type]

def convert_binary(binary):
    """Wrapper method for conversion 
    
    Parameters:
        binary
            A BinaryResource instance
    """
    result = False
    type = binary.content_type
    converter = get_converter(type)
    extension = get_extension(type)
    result = converter(binary, type, extension)
    return result