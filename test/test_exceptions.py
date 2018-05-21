# -*- encoding: utf-8 -*-
# pylint: skip-file
import unittest

from esipy.exceptions import APIException


class TestApiException(unittest.TestCase):
    URL = "http://foo.bar"
    STATUS_CODE = 404
    STATUS_CODE_STR = '404'
    ERROR_RESPONSE = {'error': 'This is an error'}
    MESSAGE_RESPONSE = {'message': 'This is a message'}
    PARAMS = {'some': 'params'}
    HEADERS = {'just': 'someheader'}

    def test_api_exception_error(self):
        e = APIException(
            TestApiException.URL,
            TestApiException.STATUS_CODE,
            json_response=TestApiException.ERROR_RESPONSE,
            request_param=TestApiException.PARAMS,
            response_header=TestApiException.HEADERS
        )

        self.assertEqual(e.url, TestApiException.URL)
        self.assertIn(TestApiException.STATUS_CODE_STR, str(e))
        self.assertIn(TestApiException.ERROR_RESPONSE['error'], str(e))
        self.assertEqual(e.request_param, TestApiException.PARAMS)
        self.assertEqual(e.response_header, TestApiException.HEADERS)

    def test_api_exception_message(self):
        e = APIException(
            TestApiException.URL,
            TestApiException.STATUS_CODE,
            json_response=TestApiException.MESSAGE_RESPONSE
        )

        self.assertEqual(e.url, TestApiException.URL)
        self.assertIn(TestApiException.STATUS_CODE_STR, str(e))
        self.assertIn(TestApiException.MESSAGE_RESPONSE['message'], str(e))
        self.assertEqual(e.request_param, {})
        self.assertEqual(e.response_header, {})

    def test_api_exception_no_message_error(self):
        e = APIException(
            TestApiException.URL,
            TestApiException.STATUS_CODE,
            json_response={}
        )

        self.assertEqual(e.url, TestApiException.URL)
        self.assertIn(TestApiException.STATUS_CODE_STR, str(e))
        self.assertNotIn(TestApiException.ERROR_RESPONSE['error'], str(e))
        self.assertNotIn(TestApiException.MESSAGE_RESPONSE['message'], str(e))
        self.assertEqual(e.request_param, {})
        self.assertEqual(e.response_header, {})
