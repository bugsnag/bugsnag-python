import unittest
import unittest.mock
import urllib.parse


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

        notification = unittest.mock.Mock()
        notification.request_config.wsgi_environ = environ

        bugsnag.wsgi.middleware.add_wsgi_request_data_to_notification(
            notification
        )

        self.assertEqual(
            'http://localhost/hello/world',
            notification.add_tab.call_args_list[0][0][1]['url']
        )

    def test_wrongly_encoded_url_should_not_raise(self):
        import bugsnag.wsgi.middleware

        environ = self.environ.copy()
        # https://github.com/python/cpython/blob/master/Lib/wsgiref/simple_server.py#L85
        environ['PATH_INFO'] = urllib.parse.unquote('/%83', 'latin-1')

        notification = unittest.mock.Mock()
        notification.request_config.wsgi_environ = environ

        bugsnag.wsgi.middleware.add_wsgi_request_data_to_notification(
            notification
        )

        self.assertEqual(
            'http://localhost/%C2%83',
            notification.add_tab.call_args_list[0][0][1]['url']
        )

    def test_path_supports_emoji(self):
        import bugsnag.wsgi.middleware

        environ = self.environ.copy()
        environ['PATH_INFO'] = '/😇'

        notification = unittest.mock.Mock()
        notification.request_config.wsgi_environ = environ

        bugsnag.wsgi.middleware.add_wsgi_request_data_to_notification(
            notification
        )

        # You can validate this by using "encodeURIComponent" in a browser.
        self.assertEqual(
            'http://localhost/%F0%9F%98%87',
            notification.add_tab.call_args_list[0][0][1]['url']
        )

    def test_path_supports_non_ascii_characters(self):
        import bugsnag.wsgi.middleware

        environ = self.environ.copy()
        environ['PATH_INFO'] = '/ôßłガ'

        notification = unittest.mock.Mock()
        notification.request_config.wsgi_environ = environ

        bugsnag.wsgi.middleware.add_wsgi_request_data_to_notification(
            notification
        )

        # You can validate this by using "encodeURIComponent" in a browser.
        self.assertEqual(
            'http://localhost/%C3%B4%C3%9F%C5%82%E3%82%AC',
            notification.add_tab.call_args_list[0][0][1]['url']
        )


if __name__ == '__main__':
    unittest.main()
