Feature: Handled exceptions

Scenario: Handled exceptions are delivered
  Given I run the service "plain" with the command "python handled.py"
  And I wait to receive an error
  Then the error is valid for the error reporting API version "4.0" for the "Python Bugsnag Notifier" notifier
  And the exception "errorClass" equals "RuntimeError"
  And the exception "message" equals "uh oh :o"
  And the event "unhandled" is false
  And the event "severity" equals "warning"
  And the event "severityReason.type" equals "handledException"
