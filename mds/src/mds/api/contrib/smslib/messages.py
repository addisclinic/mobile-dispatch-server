'''
Created on Aug 11, 2012

:author: Sana Development Team
:version: 2.0
'''
try:
    import json as simplejson
except ImportError, e:
    import simplejson
    
import logging, telnetlib
from kannel import send_kannel_notification

SMS_MESSAGE_SIZE = 140

def send_notification(n, phoneId, formatter=None):
    """Sends sms notification
    
    Parameters:
        n
            The notification.
        phoneId
            Phone number
    """
    # if phoneId == "emulator":
#         return send_fake_notification(n, phoneId)
#     else:

    # return send_clickatell_notification(n, phoneId)
    # return send_znisms_notification(n, phoneId)
    return send_kannel_notification(n, phoneId, formatter=formatter) # New default

def format_sms(n):
    """Splits a given notification over a number of SMS messages and attaches
    header information for tracking which message is which. Returns a list of
    strings that are no more than SMS_MESSAGE_SIZE characters long.
    
    Parameters:
        n
            The notfication.
    """
    encoder = simplejson.JSONEncoder(separators=(',',':'))

    data = {'n': n.id,
            'c': n.procedure_id,
            'p': n.patient_id}
    subsequent_data = {'n': n.id,
                       'd': ''}
    test = encoder.encode(data)
    test_subsequent = encoder.encode(subsequent_data)

    # We have to clean the message of all uses of right-brace, because the
    # client will look for the last right brace in the text to find where the
    # JSON header ends. Just replace all left and right braces with parens.
    cleaned_message = n.message.replace("}",")").replace("{","(")

    # Search for the largest number of messages that fit.
    satisfied = False
    messages = 0

    while not satisfied:
        messages += 1
        message = cleaned_message
        message_size = len(message)
        result = []

        if messages > 1:
            data['d'] = '%d/%d' % (1,messages)
        header = encoder.encode(data)
        header_remaining = SMS_MESSAGE_SIZE - len(header)

        if header_remaining < 0:
            raise ValueError("Can't fit message.")

        header_message = message[:header_remaining]
        message = message[header_remaining:]
        result.append(header + header_message)

        for i in xrange(2, messages+1):
            subsequent_data['d'] = '%d/%d' % (i,messages)
            subsequent_header = encoder.encode(subsequent_data)
            subsequent_remaining = SMS_MESSAGE_SIZE - len(subsequent_header)
            subsequent_message = message[:subsequent_remaining]
            message = message[subsequent_remaining:]
            result.append(subsequent_header + subsequent_message)

        if len(message) == 0:
            satisfied = True

    return result


def send_fake_notification(n, phoneId):
    """Sends a fake SMS via telnet
    
    Parameters:
        n
            The notification
        PhoneId
            a phone number
    """
    try:
        message = "<patient=%s>Patient %s : %s" % (n.patient_id, n.patient_id, n.message)
        print "Sending", message
        t = telnetlib.Telnet('127.0.0.1', 5554)
        t.read_until("OK")

        # needs to be str not unicode?
        #cmd = str("sms send %s %s\n" % (n.client, message))
        cmd = "sms send %s %s\n" % ("3179461787", str(message).replace("\n",""))
        #cmd = "sms send %s \"%s\"\n" % (str(n.client), str(n.to_json()))
        #logging.error(cmd)
        t.write(str(cmd))
        t.read_until("OK")
        t.write("exit\n")
        t.close()

        n.delivered = True
        n.save()
    except Exception, e:
        n.delivered = False
        n.save()
        logging.error("Couldn't submit notification for %s" % str(e))
