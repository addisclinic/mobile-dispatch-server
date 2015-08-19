"""Provides utilities for converting media types.

Additional media converters should be added as callables which return True upon
successful transcoding.

:Authors: Sana dev team
:Version: 1.1
"""
#TODO The above really should have used __call__
from __future__ import with_statement
import os
import logging
import subprocess


# Conversion args for ffmpeg output depending on desired file type.
# Command will be  executed as:
#
#    ffmpeg -i infile extra_arg0 extra_arg1 ... extra_argN outfile
#
# Documentation for arguments: http://www.ffmpeg.org/ffmpeg-doc.html
# Example: SOUND: [' -acodec', 'mp3', '-ar', '44100', '-ab', '64k' ]
FFMPEG_EXTRA_ARGS = {'SOUND': [],
                     'VIDEO': ['-ar', '44100','-acodec', 'libmp3lame','-sameq' ]
                     }
"""ffmpeg executable command line arguments"""

class FFmpeg:
    """Wrapper around ffmpeg
    """
    def __unicode__(self):
        return "FFMPEG"

    def __call__(self, binary, converted_type, converted_extension):
        """Reencodes binary content. Content type must be supported by ffmpeg
        build; i.e. call maybe_convert_binary_ffmpeg first.

        Parameters:
            binary
                the binary resource whose file will be encoded
            converted_type
                the output content type
            converted_extension
                extension for the output file
        """
        # Default return
        result = False
        message = "FFMPEG"

        # Create string with new path name for converted file
        converted_filename = os.path.splitext(binary.data.path)[0] + "." + \
                             converted_extension
        # base ffmpeg exec
        ffmpeg_exec = [ 'ffmpeg', '-i', binary.data.path ]

        ### TODO Do we need this?
        # Create environment variables
        os.putenv('TMPDIR', '/tmp')
        os.putenv('LD_LIBRARY_PATH', '/usr/lib')

        # Append any output codec specific args from  FFMPEG_EXTRA_ARGS
        for arg in FFMPEG_EXTRA_ARGS[binary.content_type]:
            ffmpeg_exec.append(arg)
        # Add output filename to executable.
        ffmpeg_exec.append(converted_filename)
        logging.debug('FFMPEG Call: %s' % ffmpeg_exec)
        try:
            # Execute ffmpeg and get return code
            return_code = subprocess.Popen(ffmpeg_exec, bufsize=2048,
                                       stderr=subprocess.STDOUT,
                                       stdout=subprocess.PIPE).wait()
            logging.debug('FFMPEG Return Code: %s' % return_code)

            # return code = 0 indicates success
            if return_code == 0:
                try:
                    # Preserve original name so that we can remove 3gp file
                    #original_file = binary.data.path

                    # Get size of converted data
                    # size = os.path.getsize(str(converted_filename))

                    # Update binary db fields
                    binary.data = os.path.splitext(str(binary.data))[0] + "." +\
                                  converted_extension
                    binary.content_type = converted_type
                    binary.save()
                    # TODO Remove original file - we don't need it anymore
                    #os.remove(str(original_file))
                    message = "FFMPEG: Success %s" % binary.data.path

                # Catch any errors from updating binary fields
                except Exception, e:
                    message = "Error updating binary post conversion: %s" % e
                    logging.error(message)

            # Got a non zero return code
            else:
                message = "FFMPEG failed. Bad File? Try ffmpeg -i %s" % \
                          binary.data.path

            result = True
            binary.conversion_complete = True
            binary.save()
        # Catch any errors thrown by ffmpeg execution
        except Exception, e:
            message = "Conversion error, check ffmpeg installation: %s" % e
            logging.error(message)
        return result, message

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