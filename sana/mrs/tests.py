from django.test.client import Client
from django.utils import unittest
from django.conf import settings
from haralyzer import HarParser
from os import path
import cjson
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
        c = Client()
        request = None

        with open(path.join(settings.BASE_DIR, 'data', 'upload_notification.har', 'r')) as f:
            har_parser = HarParser(cjson.decode(f.read()))

            request = har_parser.har_data['entries'][0]['request']

        response = c.post("/notifications/submit/", request['postData'])

        self.assertEqual(response.status_code, 200)