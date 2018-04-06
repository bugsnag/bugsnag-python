import os


def large_object_file_path():
    """
    Resolve the file path to the large_object.json file. This is needed by
    `test_utils.py` as the `timeit` module is not able to resolve the path to
    the file correctly.
    """
    file_path = os.path.abspath(__file__)
    directory = os.path.dirname(file_path)
    return os.path.abspath(os.path.join(directory, 'large_object.json'))
