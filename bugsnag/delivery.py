from threading import Thread, Timer
import sys

from threading import Lock
from time import strftime, gmtime

from six.moves.urllib.request import (
    Request,
    ProxyHandler,
    build_opener
)

import bugsnag
from bugsnag.utils import SanitizingJSONEncoder, merge_dicts, MAX_PAYLOAD_LENGTH

try:
    if sys.version_info < (2, 7):
        raise ImportError('requests-based delivery will fail on 2.6 '
                          'and earlier')

    if (3, 1) < sys.version_info < (3, 3):
        raise ImportError('requests-based delivery will fail on 3.2')

    import requests
except ImportError:
    requests = None


def create_default_delivery():
    if requests is not None:
        return RequestsDelivery()

    return UrllibDelivery()


class Delivery(object):
    """
    Mechanism for sending a report to Bugsnag
    """

    def __init__(self):
        self.config = None

    def deliver(self, report_payload):
        """
        Sends a report to Bugsnag
        """
        pass

    def get_default_headers(self):
        return {
            'Content-Type': 'application/json',
            'Bugsnag-Sent-At': strftime('%Y-%m-%dT%H:%M:%S', gmtime())
        }


class UrllibDelivery(Delivery):

    def deliver(self, config, payload, options = {}):

        filters = config.params_filters
        encoder = SanitizingJSONEncoder(separators=(',', ':'),
                                        keyword_filters=filters)
        encoded_payload = encoder.encode(payload)

        def request():
            if 'endpoint' in options:
                uri = options['endpoint']
            else:
                uri = config.endpoint

            headers = options['headers'] if 'headers' in options else {}
            headers.update(self.get_default_headers())

            if '://' not in uri:
                uri = config.get_endpoint()

            req = Request(uri,
                          encoded_payload.encode('utf-8', 'replace'),
                          headers)

            if config.proxy_host:
                proxies = ProxyHandler({
                    'https': config.proxy_host,
                    'http': config.proxy_host
                })

                opener = build_opener(proxies)
            else:
                opener = build_opener()

            resp = opener.open(req)
            status = resp.getcode()

            if 'success' in options:
                success = options['success']
            else:
                success = 200
            if status != success:
                bugsnag.logger.warning(
                    'Delivery to %s failed, status %d' % (uri, status))

        if config.asynchronous:
            Thread(target=request).start()
        else:
            request()


class RequestsDelivery(Delivery):

    def deliver(self, config, payload, options={}):

        filters = config.params_filters
        encoder = SanitizingJSONEncoder(separators=(',', ':'),
                                        keyword_filters=filters)
        encoded_payload = encoder.encode(payload)

        def request():
            if 'endpoint' in options:
                uri = options['endpoint']
            else:
                uri = config.endpoint

            if '://' not in uri:
                uri = config.get_endpoint()

            headers = options['headers'] if 'headers' in options else {}
            headers.update(self.get_default_headers())
            req_options = {'data': encoded_payload, 'headers': headers}

            if config.proxy_host:
                req_options['proxies'] = {
                    'https': config.proxy_host,
                    'http': config.proxy_host
                }

            response = requests.post(uri, **req_options)
            status = response.status_code
            if 'success' in options:
                success = options['success']
            else:
                success = requests.codes.ok

            if status != success:
                bugsnag.logger.warning(
                    'Delivery to %s failed, status %d' % (uri, status))

        if config.asynchronous:
            Thread(target=request).start()
        else:
            request()
