'''
'''
__all__ = [
    'parse_basic',
    'parse_auth',
]

def parse_basic(auth):
    auth = auth.strip().decode('base64')
    (username,password) =  auth.split(':', 1)
    return { 'username':username, 'password':password}
    
def parse_auth(request):
    auth_string = request.META.get('HTTP_AUTHORIZATION', None)
    if not auth_string:
        return {}
    try:
        (authmeth, auth) = auth_string.split(" ", 1)
        if authmeth.lower() == 'basic':
            return parse_basic(auth)
    except:
        return None
