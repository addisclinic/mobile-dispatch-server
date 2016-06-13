'''
'''
import cjson

class OpenMRSRESTException(Exception):
    pass

class RESTError(object):
    def __init__(self,response):
        error = response.pop('error',{})
        self.code = error.get('code', None)
        self.message = error.get('message',None)
        self.details = error.get('details',None)
        
class RESTResult(object):
    def __init__(self,response,decoder=None):
        results = response.pop('results',[])
        self.results = [decoder.decode(x) for x in results] if decoder else results

class RESTSession(object):
    def __init__(self,response):
        self.sessionId = response.pop('sessionId', None)
        self.authenticated = response.pop('authenticated', False)
        
class RESTResponse(object):
    def __init__(self, response, decoder=None):
        self._results = RESTResult(response,decoder=decoder) if response.has_key('results') else None
        self._error = RESTError(response) if response.has_key('error') else None
        self._session = RESTSession(response) if response.has_key('sessionId') else None
        self._instance = response

    def has_error(self):
        if self._error:
            return True
        else:
            return False

    def has_results(self):
        if self._results:
            return True
        else:
            return False
            
    
    def has_instance(self):
        if self._instance:
            return True
        else:
            return False

    @property
    def error(self):
        if not self.has_error():
            return False
        return self._error.message

    @property
    def results(self):
        if not self.has_results():
            return []
        return self._results.results

    @property
    def session(self):
        if not self.has_session():
            return None
        return self._session.session_id

    @property
    def instance(self):
        return self._instance
        
def decode(response, result_decoder=None):
    ''' Takes a json encoded response body and returns a RESTResponse
        instance
        
        if 'result_decoder is specified, it will be used to decode 
        any 'results'.
    '''
    response_dict = cjson.decode(response)
    result = RESTResponse(response_dict, decoder=result_decoder)
    if result.has_error():
        raise OpenMRSRestException(result.error)
    return result
