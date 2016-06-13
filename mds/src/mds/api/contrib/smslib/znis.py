'''
Created on Aug 11, 2012

:author: Sana Development Team
:version: 2.0
'''

try:
    import json as simplejson
except ImportError, e:
    import simplejson
    
import logging
import urllib

from django.conf import settings
from .messages import format_sms

def send_znisms_notification(message_body, phoneId, formatter=None):
    return ZnisOpener().open(message_body, phoneId, formatter=formatter)

class ZnisOpener:
    
    def __init__(self):
        pass
    
    def open(self, message_body, phoneId, formatter=None):
        """Sends an SMS message to ZniSMS http interface
            
        ZniSMS API documentation: http://www.znisms.com/api.pdf
            
        ZniSMS url: http://api.znisms.com/post/smsv3.asp?userid=joinus&apikey=xxx&
        message=Your+Message&senderid=9123123456&sendto=9123123457
            
        ZniSMS Request params
            userid     
                ZniSMS username
            apikey
                ZniSMS API key
            message
                SMS message body to send
            senderid
                Sender ID (should be alphanumeric)
            sendto
                Destination number (no +91, 91 or 0 in front)
            
        Parameters:
            message_body
                Message body
            phoneId
                Recipient
        """
        result = False
        try:
            messages = formatter(message_body) if formatter else message_body
            for message in messages:
    
                params = urllib.urlencode({
                        'userid': settings.ZNISMS_USER,
                        'apikey': settings.ZNISMS_APIKEY,
                        'senderid': settings.ZNISMS_SENDERID,
                        'sendto': phoneId,
                        'message': message
                        })
    
                logging.info("Sending ZniSMS notification %s to %s" %
                             (message, phoneId))
                response = urllib.urlopen(settings.ZNISMS_URL % params).read()
                logging.info("ZniSMS response: %s" % response)
                result = True
        except Exception, e:
            logging.error("Couldn't submit ZniSMS notification for %s: %s" % (phoneId, e))
        return result