Feature: Sessions in AWS Lambda

@not-python-3.5 @not-python-3.6 @not-python-3.7 @not-python-3.8
Scenario: Manually started sessions are delivered in an AWS Lambda app when auto_capture_sessions is True
  Given I run the lambda handler "manual_session" with the "event.json" event
  When I wait to receive a session
  Then the session is valid for the session reporting API version "4.0" for the "Python Bugsnag Notifier" notifier
  And the session payload has a valid sessions array
  And the sessionCount "sessionsStarted" equals 2
  And I should receive no errors

@not-python-3.5 @not-python-3.6 @not-python-3.7 @not-python-3.8
Scenario: Manually started sessions are delivered in an AWS Lambda app when auto_capture_sessions is False
  Given I run the lambda handler "manual_session_no_auto_capture_sessions" with the "event.json" event
  When I wait to receive a session
  Then the session is valid for the session reporting API version "4.0" for the "Python Bugsnag Notifier" notifier
  And the session payload has a valid sessions array
  And the sessionCount "sessionsStarted" equals 1
  And I should receive no errors
