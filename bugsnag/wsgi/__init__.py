import urllib


def request_path(env):
    return urllib.quote('/' + env.get('PATH_INFO', '').lstrip('/'))
