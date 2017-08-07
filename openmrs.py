from kivy.network.urlrequest import UrlRequest

__app_package__ = 'edu.sepsis'

import base64
import json
try:
    from urllib import quote
except ImportError:
    from urllib.parse import quote


class RESTConnection(object):
    @staticmethod
    def _construct_url(authority, port, resource):
        return 'http://{authority}:{port}/openmrs/ws/rest/v1/{resource}' \
            .format(authority=authority, port=port, resource=resource)

    def __init__(self, authority, port, username, password):
        self.authority = authority
        self.port = port
        credentials = '{username}:{password}'.format(username=username, password=password)
        credentials = base64.standard_b64encode(credentials.encode('UTF8')).decode('UTF8')
        self.headers = {
            'Authorization': 'Basic {credentials}'.format(credentials=credentials),
            'Content-type': 'application/json',
        }

    def send_request(self, resource, parameters, on_success, on_failure, on_error):
        url = RESTConnection._construct_url(self.authority, self.port, resource)
        parameters = json.dumps(parameters) if parameters is not None else None
        UrlRequest(url, req_headers=self.headers, req_body=parameters,
                   on_success=on_success, on_failure=on_failure, on_error=on_error)
