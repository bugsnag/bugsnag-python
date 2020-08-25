from urllib.parse import quote


def request_path(env):
    return quote('/' + env.get('PATH_INFO', '').lstrip('/'))
