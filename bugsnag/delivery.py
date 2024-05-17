from threading import Thread
from typing import Dict, Callable, Any
import sys
import json
import warnings

from time import strftime, gmtime

from urllib.request import (
    Request,
    ProxyHandler,
    build_opener
)

from bugsnag.event import Event

try:
    if sys.version_info < (2, 7):
        raise ImportError('requests-based delivery will fail on 2.6 '
                          'and earlier')

    if (3, 1) < sys.version_info < (3, 3):
        raise ImportError('requests-based delivery will fail on 3.2')

    import requests
except ImportError:
    requests = None  # type: ignore

DEFAULT_ENDPOINT = 'https://notify.bugsnag.com'
DEFAULT_SESSIONS_ENDPOINT = 'https://sessions.bugsnag.com'

__all__ = ('default_headers', 'Delivery')


def _noop():
    pass


def _marshall_post_delivery_callback(post_delivery_callback):
    if not callable(post_delivery_callback):
        return _noop

    def safe_post_delivery_callback():
        try:
            post_delivery_callback()
        except Exception:
            pass

    return safe_post_delivery_callback


def create_default_delivery():
    if requests is not None:
        return RequestsDelivery()

    return UrllibDelivery()


def default_headers(api_key: str):
    return {
        'Bugsnag-Api-Key': api_key,
        'Bugsnag-Payload-Version': Event.PAYLOAD_VERSION,
        'Bugsnag-Sent-At': strftime('%Y-%m-%dT%H:%M:%S', gmtime()),
        'Content-Type': 'application/json',
    }


class Delivery:
    """
    Mechanism for sending a request to Bugsnag
    """
    def __init__(self):
        self.sent_session_warning = False

    def deliver(self, config, payload: Any, options=None):
        """
        Sends error reports to Bugsnag
        """
        pass

    def deliver_sessions(self, config, payload: Any, options=None):
        """
        Sends sessions to Bugsnag
        """
        if (config.endpoint != DEFAULT_ENDPOINT and config.session_endpoint ==
                DEFAULT_SESSIONS_ENDPOINT):
            if not self.sent_session_warning:
                warnings.warn('The session endpoint has not been configured. '
                              'No sessions will be sent to Bugsnag.')
                self.sent_session_warning = True
        else:
            if options is None:
                options = {}

            options['endpoint'] = config.session_endpoint

            self.deliver(config, payload, options)

    def queue_request(self, request: Callable, config, options: Dict):
        post_delivery_callback = _marshall_post_delivery_callback(
            options.pop('post_delivery_callback', None)
        )

        if config.asynchronous and options.pop('asynchronous', True):
            # if an exception escapes the thread, our threading.excepthook
            # will catch it and attempt to deliver it
            # this will cause an infinite loop if delivery can never succeed,
            # e.g. because the URL is unreachable
            def safe_request():
                try:
                    request()
                except Exception as e:
                    config.logger.exception('Notifying Bugsnag failed %s', e)
                finally:
                    post_delivery_callback()

            Thread(target=safe_request).start()
        else:
            try:
                request()
            finally:
                post_delivery_callback()


class UrllibDelivery(Delivery):
    def deliver(self, config, payload: Any, options=None):
        if options is None:
            options = {}

        def request():
            uri = options.pop('endpoint', config.endpoint)
            if '://' not in uri:
                uri = ('https://{}' % uri)
            api_key = json.loads(payload).pop('apiKey', config.api_key)
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
                # if an expected status code has been given then it must match
                # exactly with the actual status code
                success = status == options['success']
            else:
                # warn if we don't get a 2xx status code by default
                success = status >= 200 and status < 300

            if not success:
                config.logger.warning(
                    'Delivery to %s failed, status %d' % (uri, status)
                )

        self.queue_request(request, config, options)


class RequestsDelivery(Delivery):
    def deliver(self, config, payload: Any, options=None):
        if options is None:
            options = {}

        def request():
            uri = options.pop('endpoint', config.endpoint)
            if '://' not in uri:
                uri = ('https://{}' % uri)

            api_key = json.loads(payload).pop('apiKey', config.api_key)
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
                # if an expected status code has been given then it must match
                # exactly with the actual status code
                success = status == options['success']
            else:
                # warn if we don't get a 2xx status code by default
                success = status >= 200 and status < 300

            if not success:
                config.logger.warning(
                    'Delivery to %s failed, status %d' % (uri, status)
                )

        self.queue_request(request, config, options)
