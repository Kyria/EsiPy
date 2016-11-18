# -*- encoding: utf-8 -*-


class APIException(Exception):
    def __init__(self, url, code, json_response):
        self.url = url
        self.status_code = code
        self.response = json_response

    def __str__(self):
        if 'error' in self.response:
            return 'HTTP Error %s: %s' % (self.status_code,
                                          self.response['error'])
        elif 'message' in self.response:
            return 'HTTP Error %s: %s' % (self.status_code,
                                          self.response['message'])
        else:
            return 'HTTP Error %s' % (self.status_code)
