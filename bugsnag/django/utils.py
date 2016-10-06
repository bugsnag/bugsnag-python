from __future__ import print_function, absolute_import


class MiddlewareMixin(object):
    def __init__(self, get_response=None):
        super(MiddlewareMixin, self).__init__()
