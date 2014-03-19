from bugsnag.configuration import Configuration
import os
import socket

def test_get_endpoint():
    # Test default endpoint with ssl
    c = Configuration()
    c.use_ssl = True
    assert(c.get_endpoint() == "https://notify.bugsnag.com")

    # Test default endpoint without ssl
    c = Configuration()
    c.use_ssl = False
    assert(c.get_endpoint() == "http://notify.bugsnag.com")

    # Test custom endpoint
    c = Configuration()
    c.use_ssl = False
    c.endpoint = "localhost:1234"
    assert(c.get_endpoint() == "http://localhost:1234")

def test_environment_defaults():
    os.environ['BUGSNAG_API_KEY'] = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    c = Configuration()
    assert(c.api_key == 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
    assert(c.project_root == os.getcwd())

def test_should_notify():
    # Test custom release_stage
    c = Configuration()
    c.release_stage = "anything"
    assert(c.should_notify() == True)

    # Test release_stage in notify_release_stages
    c = Configuration()
    c.notify_release_stages = ["production"]
    c.release_stage = "development"
    assert(c.should_notify() == False)

    # Test release_stage in notify_release_stages
    c = Configuration()
    c.notify_release_stages = ["custom"]
    c.release_stage = "custom"
    assert(c.should_notify() == True)

def test_ignore_classes():
    # Test ignoring a class works
    c = Configuration()
    c.ignore_classes.append("SystemError")
    assert(c.should_ignore(SystemError("Example")) == True)

    c = Configuration()
    c.ignore_classes.append("SystemError")
    assert(c.should_ignore(Exception("Example")) == False)

def test_hostname():
    c = Configuration()
    assert(c.hostname == socket.gethostname())

    os.environ["DYNO"] = "YES"
    c = Configuration()
    assert(c.hostname == None)