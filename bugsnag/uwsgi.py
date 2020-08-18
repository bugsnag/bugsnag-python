import warnings

running_uwsgi = False
threads_enabled = False

# From docs (https://uwsgi-docs.readthedocs.io/en/latest/PythonModule.html):
# > The uWSGI server automagically adds a uwsgi module into your Python
#   apps.
# > This is useful for configuring the uWSGI server, use its internal
#   functions and get statistics. Also useful for detecting whether you're
#   actually running under uWSGI; if you attempt to import uwsgi and
#   receive an ImportError you're not running under uWSGI.
try:
    # > uwsgi.opt
    # > The current configuration options, including any custom placeholders.
    from uwsgi import opt
    running_uwsgi = True
    threads_enabled = opt.get('enable-threads', False)
except ImportError:
    pass

__all__ = ('warn_if_running_uwsgi_without_threads',)


def warn_if_running_uwsgi_without_threads():
    if running_uwsgi and not threads_enabled:
        warnings.warn(('Bugsnag cannot run asynchronously under uWSGI' +
                       ' without enabling thread support. Please run uwsgi' +
                       ' with --enable-threads'), RuntimeWarning)
