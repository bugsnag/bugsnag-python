Feature: Celery

Scenario Outline: Handled exceptions are delivered in Celery <celery-version>
  Given I start the service "celery-<celery-version>"
  When I execute the command "python bugsnag_celery_test_app/queue_task.py handled" in the service "celery-<celery-version>"
  And I wait to receive an error
  Then the error is valid for the error reporting API version "4.0" for the "Python Bugsnag Notifier" notifier
  And the exception "errorClass" equals "Exception"
  And the exception "message" equals "oooh nooo"
  And the event "unhandled" is false
  And the event "severity" equals "warning"
  And the event "severityReason.type" equals "handledException"
  And the event "device.runtimeVersions.celery" matches "<celery-version>\.\d+\.\d+"

  @not-python-3.11 @not-python-3.12
  Examples:
    | celery-version |
    |              4 |

  @not-python-3.5
  Examples:
    | celery-version |
    |              5 |

Scenario Outline: Unhandled exceptions are delivered in Celery <celery-version>
  Given I start the service "celery-<celery-version>"
  When I execute the command "python bugsnag_celery_test_app/queue_task.py unhandled" in the service "celery-<celery-version>"
  And I wait to receive an error
  Then the error is valid for the error reporting API version "4.0" for the "Python Bugsnag Notifier" notifier
  And the exception "errorClass" equals "KeyError"
  And the exception "message" equals "'b'"
  And the event "unhandled" is true
  And the event "severity" equals "error"
  And the event "severityReason.type" equals "unhandledExceptionMiddleware"
  And the event "severityReason.attributes.framework" equals "Celery"
  And the event "device.runtimeVersions.celery" matches "<celery-version>\.\d+\.\d+"
  And the event "context" equals "bugsnag_celery_test_app.tasks.unhandled"
  And the event "metaData.extra_data.task_id" is not null
  # these aren't strings but the maze runner step works on arrays and hashes
  And the event "metaData.extra_data.args" string is empty
  And the event "metaData.extra_data.kwargs" string is empty

  @not-python-3.11 @not-python-3.12
  Examples:
    | celery-version |
    |              4 |

  @not-python-3.5
  Examples:
    | celery-version |
    |              5 |

Scenario Outline: Task arguments are added to metadata in Celery <celery-version>
  Given I start the service "celery-<celery-version>"
  When I execute the command "python bugsnag_celery_test_app/queue_task.py add 1 2 3 '4' a=100 b=200" in the service "celery-<celery-version>"
  And I wait to receive an error
  Then the error is valid for the error reporting API version "4.0" for the "Python Bugsnag Notifier" notifier
  And the exception "errorClass" equals "AssertionError"
  And the exception "message" equals ""
  And the event "unhandled" is true
  And the event "severity" equals "error"
  And the event "severityReason.type" equals "unhandledExceptionMiddleware"
  And the event "severityReason.attributes.framework" equals "Celery"
  And the event "device.runtimeVersions.celery" matches "<celery-version>\.\d+\.\d+"
  And the event "context" equals "bugsnag_celery_test_app.tasks.add"
  And the event "metaData.extra_data.task_id" is not null
  And the error payload field "events.0.metaData.extra_data.args" is an array with 4 elements
  And the event "metaData.extra_data.args.0" equals "1"
  And the event "metaData.extra_data.args.1" equals "2"
  And the event "metaData.extra_data.args.2" equals "3"
  And the event "metaData.extra_data.args.3" equals "4"
  And the event "metaData.extra_data.kwargs.a" equals "100"
  And the event "metaData.extra_data.kwargs.b" equals "200"

  @not-python-3.11 @not-python-3.12
  Examples:
    | celery-version |
    |              4 |

  @not-python-3.5
  Examples:
    | celery-version |
    |              5 |

Scenario Outline: Errors in shared tasks are reported in Celery <celery-version>
  Given I start the service "celery-<celery-version>"
  When I execute the command "python bugsnag_celery_test_app/queue_task.py divide 10 0" in the service "celery-<celery-version>"
  And I wait to receive an error
  Then the error is valid for the error reporting API version "4.0" for the "Python Bugsnag Notifier" notifier
  And the exception "errorClass" equals "ZeroDivisionError"
  And the exception "message" equals "division by zero"
  And the event "unhandled" is true
  And the event "severity" equals "error"
  And the event "severityReason.type" equals "unhandledExceptionMiddleware"
  And the event "severityReason.attributes.framework" equals "Celery"
  And the event "device.runtimeVersions.celery" matches "<celery-version>\.\d+\.\d+"
  And the event "context" equals "bugsnag_celery_test_app.tasks.divide"
  And the event "metaData.extra_data.task_id" is not null
  And the error payload field "events.0.metaData.extra_data.args" is an array with 2 elements
  And the event "metaData.extra_data.args.0" equals "10"
  And the event "metaData.extra_data.args.1" equals "0"
  And the event "metaData.extra_data.kwargs" string is empty

  @not-python-3.11 @not-python-3.12
  Examples:
    | celery-version |
    |              4 |

  @not-python-3.5
  Examples:
    | celery-version |
    |              5 |

Scenario Outline: Successful tasks do not report errors in Celery <celery-version>
  Given I start the service "celery-<celery-version>"
  When I execute the command "python bugsnag_celery_test_app/queue_task.py add 1 2 3 4 5 6 7 a=8 b=9" in the service "celery-<celery-version>"
  Then I should receive no errors

  @not-python-3.11 @not-python-3.12
  Examples:
    | celery-version |
    |              4 |

  @not-python-3.5
  Examples:
    | celery-version |
    |              5 |

Scenario Outline: Successful shared tasks do not report errors in Celery <celery-version>
  Given I start the service "celery-<celery-version>"
  When I execute the command "python bugsnag_celery_test_app/queue_task.py divide 10 2" in the service "celery-<celery-version>"
  Then I should receive no errors

  @not-python-3.11 @not-python-3.12
  Examples:
    | celery-version |
    |              4 |

  @not-python-3.5
  Examples:
    | celery-version |
    |              5 |
