from threading import Thread
import sys
import json

from time import strftime, gmtime

from six.moves.urllib.request import (
    Request,
    ProxyHandler,
    build_opener
)

import bugsnag
from bugsnag.notification import Notification

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


def default_headers(api_key):
    return {
        'Bugsnag-Api-Key': api_key,
        'Bugsnag-Payload-Version': Notification.PAYLOAD_VERSION,
        'Bugsnag-Sent-At': strftime('%Y-%m-%dT%H:%M:%S', gmtime()),
        'Content-Type': 'application/json',
    }


class Delivery(object):
    """
    Mechanism for sending a request to Bugsnag
    """

    def deliver(self, config, payload):
        """
        Sends error reports to Bugsnag
        """
        pass

    def deliver_sessions(self, config, payload):
        """
        Sends sessions to Bugsnag
        """
        pass


class UrllibDelivery(Delivery):

    def deliver_sessions(self, config, payload):
        options = {
            'endpoint': config.session_endpoint,
            'success': 202,
        }
        self.deliver(config, payload, options)

    def deliver(self, config, payload, options={}):

        def request():
            uri = options.pop('endpoint', config.endpoint)
            if '://' not in uri:
                uri = config.get_endpoint()
            api_key = json.loads(payload).pop('apiKey', config.get('api_key'))
            req = Request(uri,
                          payload.encode('utf-8', 'replace'),
                          default_headers(api_key))

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

    def deliver_sessions(self, config, payload):
        options = {
            'endpoint': config.session_endpoint,
            'success': 202,
        }
        self.deliver(config, payload, options)

    def deliver(self, config, payload, options={}):

        def request():
            uri = options.pop('endpoint', config.endpoint)
            if '://' not in uri:
                uri = config.get_endpoint()

            api_key = json.loads(payload).pop('apiKey', config.get('api_key'))
            req_options = {'data': payload,
                           'headers': default_headers(api_key)}

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
