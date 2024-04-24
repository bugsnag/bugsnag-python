Feature: Unhandled exceptions

Scenario: Unhandled exceptions are delivered
  Given I run the service "plain" with the command "python unhandled.py"
  And I wait to receive an error
  Then the error is valid for the error reporting API version "4.0" for the "Python Bugsnag Notifier" notifier
  And the exception "errorClass" equals "Exception"
  And the exception "message" equals "OH NO!"
  And the event "unhandled" is true
  And the event "severity" equals "error"
  And the event "severityReason.type" equals "unhandledException"
