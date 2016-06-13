''' 
Mapping objects for translating between internal and external 
representations.
'''
class FieldException(Exception):
    pass

class EncoderException(Exception):
    pass

class DecoderException(Exception):
    pass

class FieldMap(object):
    name = None
    field_name = None
    value = None

    def __init__(self, name, field_name=None, value=None):
        self.remote_name = name
        self.value = value
        self.field_name

    def __get__(self, instance, owner):
        return self.value

    def __set__(self, instance, value):
        self.value = value


class Encoder(object):

    def encode(self, instance):
        '''  generate remote representation from local instance
        '''
        raise EncoderException("Not implemented!")

class Decoder(object):

    def decode(self, instance):
        '''  generate local representation from remote instance
        '''
        raise DecoderException("Not implemented!")


class TransformBase(Encoder, Decoder):
    ''' Base class for transforming objects between local
        representation and remote.
        
        The naming convention is to "decode" remote representations
        into local and "encode" local representations into remote.
    '''

    def read(self, instance):
        ''' Convenience wrapper for decode '''
        return self.decode(instance)
        
    def write(self, instance):
        ''' Convenience wrapper for encode '''
        return self.encode(instance)

    def get_value(self, field, instance):
        ''' Returns dict key value or class instance field value '''

class ModelTransform(TransformBase):
    ''' Extend this class to implement transforms between Django model 
        instances and remote representation .
    '''
    model = None
    uri = None

    def __init__(self, model, uri=None):
        self.model = model
        self.uri = uri

def get_field_value(field, instance, default=None):
    ''' Returns dict key value or class instance field value 
        This is effectively a convenience wrapper to check whether
        instance is a dict or object to determine whether to use
        dict.get or getattr
    '''
    if not field:
        raise FieldException('None not allowed for field name')
    try:
        if isinstance(instance, dict):
            value = instance.get(field, default) if default else instance.get(field)
        elif isinstance(instance, object):
            value = getattr(instance, field,default) if default else getattr(instance,field)
    except Exception, e:
        raise FieldException('Instance has no ield %s' % field, e)
    return value
    