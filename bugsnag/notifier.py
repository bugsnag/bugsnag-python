import os

# Read version from VERSION file
_version_file = os.path.join(os.path.dirname(__file__), '..', 'VERSION')
try:
    with open(_version_file, 'r') as f:
        _version = f.read().strip()
except Exception:
    _version = 'unknown'

_NOTIFIER_INFORMATION = {
    'name': 'Python Bugsnag Notifier',
    'url': 'https://github.com/bugsnag/bugsnag-python',
    'version': _version
}
