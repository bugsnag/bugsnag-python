import inspect
import traceback

import bugsnag


MAX_STRING_LENGTH = 1024


def sanitize_object(obj, **kwargs):
    filters = kwargs.get("filters", [])

    if isinstance(obj, dict):
        clean_dict = {}
        for k, v in obj.iteritems():
            # Remove values for keys matching filters
            if any(f in k for f in filters):
                clean_dict[k] = "[FILTERED]"
            else:
                clean_obj = sanitize_object(v, **kwargs)
                if clean_obj:
                    clean_dict[k] = clean_obj

        return clean_dict
    elif any(isinstance(obj, t) for t in (list, set, tuple)):
        return [sanitize_object(x, **kwargs) for x in obj]
    else:
        try:
            if isinstance(obj, unicode):
                string = obj
            else:
                string = unicode(str(obj), errors='replace')

        except Exception:
            exc = traceback.format_exc()
            bugsnag.warn("Could not add object to metadata: %s" % exc)
            string = "[BADENCODING]"

        return string[:MAX_STRING_LENGTH]


def fully_qualified_class_name(obj):
    module = inspect.getmodule(obj)
    if module is not None and module.__name__ != "__main__":
        return module.__name__ + "." + obj.__class__.__name__
    else:
        return obj.__class__.__name__


def package_version(package_name):
    try:
        import pkg_resources
    except ImportError:
        return None
    else:
        try:
            return pkg_resources.get_distribution(package_name).version
        except pkg_resources.DistributionNotFound:
            return None
