# -*- encoding: utf-8 -*-
""" Exceptions for EsiPy related errors """


class APIException(Exception):
    """ Exception for SSO related errors """

    def __init__(self, url, code, **kwargs):
        self.url = url
        self.status_code = code
        self.response = kwargs.pop('response', '{}')
        self.request_param = kwargs.pop('request_param', {})
        self.response_header = kwargs.pop('response_header', {})
        super(APIException, self).__init__(str(self))

    def __str__(self):
        return 'HTTP Error %s: %s' % (self.status_code, self.response)
