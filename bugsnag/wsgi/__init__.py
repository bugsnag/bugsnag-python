from six.moves import urllib


def request_path(env):
    return urllib.parse.quote('/' + env.get('PATH_INFO', '').lstrip('/'))
