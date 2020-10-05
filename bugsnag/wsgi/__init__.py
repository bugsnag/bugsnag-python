from typing import Dict
from urllib.parse import quote


def request_path(env: Dict):
    return quote('/' + env.get('PATH_INFO', '').lstrip('/'))
