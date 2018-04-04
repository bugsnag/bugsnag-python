import os
import json

def large_object_file_path():
    """
    Resolve the file path to the large_object.json file. This is needed by
    `test_utils.py` as the `timeit` module is not able to resolve the path to
    the file correctly.
    """
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'large_object.json'))
