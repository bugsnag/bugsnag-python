# coding=utf-8

import unittest
from urllib.parse import quote

from bugsnag.event import Event
from bugsnag.configuration import (Configuration, RequestConfiguration)


class PathEncodingTest(unittest.TestCase):
    environ = {
        'SCRIPT_NAME': '',
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '80',
        'wsgi.url_scheme': 'http',
    }

    def test_path_supports_ascii_characters(self):
        import bugsnag.wsgi.middleware

        environ = self.environ.copy()
        environ['PATH_INFO'] = '/hello/world'

        bugsnag.configure_request(wsgi_environ=environ)

        config = Configuration()
        event = Event(
            Exception("oops"),
            config,
            RequestConfiguration.get_instance()
        )

        bugsnag.wsgi.middleware.add_wsgi_request_data_to_notification(
            event
        )

        self.assertEqual(
            'http://localhost/hello/world',
            event.metadata['request']['url']
        )

    def test_wrongly_encoded_url_should_not_raise(self):
        import bugsnag.wsgi.middleware

        environ = self.environ.copy()
        environ['PATH_INFO'] = '/%83'

        bugsnag.configure_request(wsgi_environ=environ)

        config = Configuration()
        event = Event(
            Exception("oops"),
            config,
            RequestConfiguration.get_instance()
        )

        bugsnag.wsgi.middleware.add_wsgi_request_data_to_notification(
            event
        )

        # We have to use "urllib.parse.quote" here because the exact output
        # differs on different Python versions because of how they handle
        # invalid encoding sequences
        self.assertEqual(
            'http://localhost/%s' % quote('%83'),
            event.metadata['request']['url']
        )

    def test_path_supports_emoji(self):
        import bugsnag.wsgi.middleware

        environ = self.environ.copy()
        environ['PATH_INFO'] = '/😇'

        config = Configuration()
        event = Event(
            Exception("oops"),
            config,
            RequestConfiguration.get_instance()
        )

        bugsnag.configure_request(wsgi_environ=environ)

        bugsnag.wsgi.middleware.add_wsgi_request_data_to_notification(
            event
        )

        # You can validate this by using "encodeURIComponent" in a browser.
        self.assertEqual(
            'http://localhost/%F0%9F%98%87',
            event.metadata['request']['url']
        )

    def test_path_supports_non_ascii_characters(self):
        import bugsnag.wsgi.middleware

        environ = self.environ.copy()
        environ['PATH_INFO'] = '/ôßłガ'

        config = Configuration()
        event = Event(
            Exception("oops"),
            config,
            RequestConfiguration.get_instance()
        )

        bugsnag.configure_request(wsgi_environ=environ)

        bugsnag.wsgi.middleware.add_wsgi_request_data_to_notification(
            event
        )

        # You can validate this by using "encodeURIComponent" in a browser.
        self.assertEqual(
            'http://localhost/%C3%B4%C3%9F%C5%82%E3%82%AC',
            event.metadata['request']['url']
        )


if __name__ == '__main__':
    unittest.main()
