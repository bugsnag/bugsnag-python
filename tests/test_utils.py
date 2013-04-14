from bugsnag.utils import sanitize_object

def test_sanitize_object():
    filters = ["password", "credit_card"]
    crazy_dict = {
        "password": "123456",
        "metadata": {
            "another_password": "123456",
            "regular": "text"
        },
        "bad_utf8": "a test of \xe9 char",
        "list": ["list", "of", "things"],
        "unicode": u"string",
        "obj": Exception(),
        "valid_unicode": u"\u2603",
    }

    # Sanitize our object
    sane_dict = sanitize_object(crazy_dict, filters=filters)

    # Check the values have been sanitized
    assert(sane_dict["password"] == "[FILTERED]")
    assert(sane_dict["metadata"]["another_password"] == "[FILTERED]")
    assert(sane_dict["metadata"]["regular"] == "text")
    assert("things" in sane_dict["list"])
