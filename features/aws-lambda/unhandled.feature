Feature: Unhandled exceptions in AWS Lambda

@not-python-3.5 @not-python-3.6 @not-python-3.7 @not-python-3.8
Scenario: Unhandled exceptions are delivered in an AWS Lambda app
  Given I run the lambda handler "unhandled" with the "event.json" event
  When I wait to receive an error
  Then the error is valid for the error reporting API version "4.0" for the "Python Bugsnag Notifier" notifier
  And the event "unhandled" is true
  And the event "severity" equals "error"
  And the event "severityReason.type" equals "unhandledException"
  And the exception "errorClass" equals "Exception"
  And the exception "message" equals "uh oh!"
  And the exception "type" equals "python"
  And the "file" of stack frame 0 equals "unhandled.py"
  And the event "metaData.AWS Lambda Context.function_name" equals "BugsnagAwsLambdaTestFunction"
  And the event "metaData.AWS Lambda Context.aws_request_id" is not null
  And the event "metaData.AWS Lambda Event.path" equals "/hello"
  And the event "metaData.AWS Lambda Event.httpMethod" equals "GET"
  When I wait to receive a session
  Then the session is valid for the session reporting API version "4.0" for the "Python Bugsnag Notifier" notifier
  And the session payload has a valid sessions array
  And the sessionCount "sessionsStarted" equals 1

@not-python-3.5 @not-python-3.6 @not-python-3.7 @not-python-3.8
Scenario: Unhandled exceptions are not delivered in an AWS Lambda app when auto_detect_errors is False
  Given I run the lambda handler "unhandled_no_auto_notify" with the "event.json" event
  When I wait to receive a session
  Then the session is valid for the session reporting API version "4.0" for the "Python Bugsnag Notifier" notifier
  And the session payload has a valid sessions array
  And the sessionCount "sessionsStarted" equals 1
  And I should receive no errors
