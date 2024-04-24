Feature: Handled exceptions in AWS Lambda

# 3.9 is currently the minimum python version with a lambda runtime
@not-python-3.5 @not-python-3.6 @not-python-3.7 @not-python-3.8
Scenario: Handled exceptions are delivered in an AWS Lambda app
  Given I run the lambda handler "handled" with the "event.json" event
  When I wait to receive an error
  Then the error is valid for the error reporting API version "4.0" for the "Python Bugsnag Notifier" notifier
  And the event "unhandled" is false
  And the event "severity" equals "warning"
  And the event "severityReason.type" equals "handledException"
  And the exception "errorClass" equals "Exception"
  And the exception "message" equals "hello there"
  And the exception "type" equals "python"
  And the "file" of stack frame 0 equals "handled.py"
  And the event "metaData.AWS Lambda Context.function_name" equals "BugsnagAwsLambdaTestFunction"
  And the event "metaData.AWS Lambda Context.aws_request_id" is not null
  And the event "metaData.AWS Lambda Event.path" equals "/hello"
  And the event "metaData.AWS Lambda Event.httpMethod" equals "GET"
  When I wait to receive a session
  Then the session is valid for the session reporting API version "4.0" for the "Python Bugsnag Notifier" notifier
  And the session payload has a valid sessions array
  And the sessionCount "sessionsStarted" equals 1

@not-python-3.5 @not-python-3.6 @not-python-3.7 @not-python-3.8
Scenario: Handled exceptions are delivered in an AWS Lambda app when auto_notify is False
  Given I run the lambda handler "handled_no_auto_notify" with the "event.json" event
  When I wait to receive an error
  Then the error is valid for the error reporting API version "4.0" for the "Python Bugsnag Notifier" notifier
  And the event "unhandled" is false
  And the event "severity" equals "warning"
  And the event "severityReason.type" equals "handledException"
  And the exception "errorClass" equals "Exception"
  And the exception "message" equals "hi friend"
  And the exception "type" equals "python"
  And the "file" of stack frame 0 equals "handled_no_auto_notify.py"
  And the event "metaData.AWS Lambda Context.function_name" equals "BugsnagAwsLambdaTestFunction"
  And the event "metaData.AWS Lambda Context.aws_request_id" is not null
  And the event "metaData.AWS Lambda Event.path" equals "/hello"
  And the event "metaData.AWS Lambda Event.httpMethod" equals "GET"
  When I wait to receive a session
  Then the session is valid for the session reporting API version "4.0" for the "Python Bugsnag Notifier" notifier
  And the session payload has a valid sessions array
  And the sessionCount "sessionsStarted" equals 1
