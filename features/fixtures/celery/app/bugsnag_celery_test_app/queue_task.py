import sys
import json
import bugsnag_celery_test_app.tasks as tasks


if __name__ == '__main__':
    task = sys.argv[1]
    arguments = []
    keyword_arguments = {}

    if len(sys.argv) > 2:
        raw_arguments = sys.argv[2:]

        for argument in raw_arguments:
            if '=' in argument:
                key, value = argument.split('=')
                keyword_arguments[key] = value
            else:
                arguments.append(argument)

    print("~*~ Queueing task '%s' with args: [%s] and kwargs: %s" % (task, ", ".join(arguments), json.dumps(keyword_arguments)))

    getattr(tasks, task).delay(*arguments, **keyword_arguments)
