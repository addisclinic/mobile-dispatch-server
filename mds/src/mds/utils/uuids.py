''' Utility functions for handling uuids
'''
import re
from django.utils.translation import ugettext as _

__all__ = [
    'ANY',
    'V1',
    'V2',
    'V3',
    'V4',
    'V5',
    'UUID_FORMAT',
    'UUID1_FORMAT',
    'UUID2_FORMAT',
    'UUID3_FORMAT',
    'UUID4_FORMAT',
    'UUID5_FORMAT',
    'is_valid',
]

ANY = 0
V1 = 1
V2 = 2
V3 = 3
V4 = 4
V5 = 5

UUID_FORMAT = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
UUID1_FORMAT = '[0-9a-f]{8}-[0-9a-f]{4}-1[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}'
UUID2_FORMAT = '[0-9a-f]{8}-[0-9a-f]{4}-2[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}'
UUID3_FORMAT = '[0-9a-f]{8}-[0-9a-f]{4}-3[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}'
UUID4_FORMAT = '[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}'
UUID5_FORMAT = '[0-9a-f]{8}-[0-9a-f]{4}-5[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}'

_uuidhex = re.compile(UUID_FORMAT, re.I)
_uuid1hex = re.compile(UUID1_FORMAT, re.I)
_uuid2hex = re.compile(UUID2_FORMAT, re.I)
_uuid3hex = re.compile(UUID3_FORMAT, re.I)
_uuid4hex = re.compile(UUID4_FORMAT, re.I)
_uuid5hex = re.compile(UUID5_FORMAT, re.I)


class InvalidVersionException(Exception):
    def __unicode__(self):
        message = self.message if self.message else None
        return unicode("Invalid version string.").format(unicode(message))

def validate(uuid, version=ANY):
    ''' Validates a str object is a valid format.
    '''
    regex = None
    if version == ANY:
        regex = _uuidhex
    elif version == V1:
        regex = _uuid1hex
    elif version == V2:
        regex = _uuid2hex
    elif version == V3:
        regex = _uuid3hex
    elif version == V4:
        regex = _uuid4hex
    elif version == V5:
        regex = _uuid5hex
    # Throw if no match
    if not regex:
        raise InvalidVersionException(version)

    match = regex.match(uuid)
    return bool(match)