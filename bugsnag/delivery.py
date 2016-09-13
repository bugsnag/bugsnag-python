import threading
import sys

from six.moves.urllib.request import (
    Request,
    ProxyHandler,
    build_opener
)

import bugsnag

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

    def deliver(self, report_payload):
        """
        Sends a report to Bugsnag
        """
        pass


class UrllibDelivery(Delivery):

    def deliver(self, config, payload):

        def request():
            endpoint = config.endpoint
            if '://' not in endpoint:
                endpoint = config.get_endpoint()

            req = Request(endpoint,
                          payload.encode('utf-8', 'replace'),
                          {'Content-Type': 'application/json'})

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

            if status != 200:
                bugsnag.logger.warning(
                    'Notification to %s failed, status %d' % (config.endpoint,
                                                              status))
        if config.asynchronous:
            t = threading.Thread(target=request)
            t.start()
        else:
            request()


class RequestsDelivery(Delivery):

    def deliver(self, config, payload):

        def request():
            endpoint = config.endpoint
            if '://' not in endpoint:
                endpoint = config.get_endpoint()

            headers = {'Content-Type': 'application/json'}
            options = {'data': payload, 'headers': headers}

            if config.proxy_host:
                options['proxies'] = {
                    'https': config.proxy_host,
                    'http': config.proxy_host
                }

            response = requests.post(endpoint, **options)
            status = response.status_code

            if status != requests.codes.ok:
                bugsnag.logger.warning(
                    'Notification to %s failed, status %d' % (endpoint,
                                                              status))
        if config.asynchronous:
            t = threading.Thread(target=request)
            t.start()
        else:
            request()
