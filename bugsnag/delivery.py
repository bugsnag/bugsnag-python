from threading import Thread, Timer
import sys

from time import strftime, gmtime

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

    BACKOFF_TIMES = (0.5, 1.0, 3.0, 5.0, 10.0, 30.0, 60.0, 180.0, 300.0, 600.0)

    def deliver(self, report_payload):
        """
        Sends a report to Bugsnag
        """
        pass

    def backoff(self, config, payload, endpoint, headers, request, backoff):
        try:
            if backoff is True:
                interval = self.BACKOFF_TIMES[0]
                backoff = 1
            else:
                interval = self.BACKOFF_TIMES[backoff]
                backoff += 1
            Timer(interval=interval, function=request,
                  args=(config, payload, endpoint, headers, backoff)).start()
        except IndexError:
            bugsnag.logger.warning(
                'Delivery to %s failed after %d retries' % (endpoint, backoff))


class UrllibDelivery(Delivery):

    def deliver(self, config, payload,
                endpoint=None, headers={}, backoff=False):

        def request():
            uri = endpoint or config.endpoint
            headers.update({'Content-Type': 'application/json'})
            if '://' not in uri:
                uri = config.get_endpoint()

            req = Request(uri,
                          payload.encode('utf-8', 'replace'),
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

            if status not in (200, 202):
                bugsnag.logger.warning(
                    'Delivery to %s failed, status %d' % (uri, status))
                if backoff:
                    self.backoff(config, payload, uri,
                                 headers, self.deliver, backoff)
                
        if config.asynchronous:
            Thread(target=request).start()
        else:
            request()


class RequestsDelivery(Delivery):

    def deliver(self, config, payload,
                endpoint=None, headers={}, backoff=False):

        def request():
            uri = endpoint or config.endpoint
            if '://' not in uri:
                uri = config.get_endpoint()

            headers.update({
                'Content-Type': 'application/json',
                'Bugsnag-Sent-At': strftime('%y-%m-%dT%H:%M:%S', gmtime())})
            options = {'data': payload, 'headers': headers}

            if config.proxy_host:
                options['proxies'] = {
                    'https': config.proxy_host,
                    'http': config.proxy_host
                }

            response = requests.post(uri, **options)
            status = response.status_code

            if status != requests.codes.ok:
                bugsnag.logger.warning(
                    'Notification to %s failed, status %d' % (uri,
                                                              status))
                if backoff:
                    self.backoff(config, payload, uri,
                                 headers, self.deliver, backoff)
            
        if config.asynchronous:
            Thread(target=request).start()
        else:
            request()
