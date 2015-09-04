from django.test.client import Client
from django.utils import unittest
from django.conf import settings
from haralyzer import HarParser
from os import path
from django.contrib.auth.models import User
import cjson
import subprocess
import requests
from pprint import pprint

class APITestCase(unittest.TestCase):
    def test_upload_procedure(self):
        c = Client()
        request = None

        # Load the upload data in from HAR
        with open(path.join(settings.BASE_DIR, 'data', 'upload_procedure.har'), 'r') as f:
            har_parser = HarParser(cjson.decode(f.read()))

            request = har_parser.har_data['entries'][0]['request']

        response = c.post("/json/procedure/submit/", request['postData'])

        self.assertEqual(response.status_code, 200)

    def test_upload_notification(self):
        
        user = User.objects.create_user('John', email=None, password='johnpassword')
        user.save()

        c = Client()
        
        self.assertEqual(c.login(username='John',password='johnpassword'), True)

        url = "/notifications/submit/"

        payload = {"phoneIdentifier": '1234567890',
                "notificationText": '"Hello, world"',
                "patientIdentifier": '123456789',
                "caseIdentifier": '01234'
        }

        response = c.post(url, data=payload)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(cjson.decode(response.content)['status'], 'FAILURE')