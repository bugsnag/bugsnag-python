import bugsnag
from bugsnag.configuration import Configuration

class BugsnagHandler(logging.Handler):
    def emit(self, record):
        try:
            request = record.request

            # This is specific to Django projects
            bugsnag.configure_request(session_data=dict(request.session),
                    environment_data=dict(request.META),
                    request_data=dict(request.POST))
        except:
            pass
        else:
            configuration = Configuration()
            exception = record.exc_info
            if exception:
                exc_type, exc_value, exc_tb = exception
                bugsnag_module_path = os.path.dirname(bugsnag.__file__)

                stacktrace = []
                for line in exc_tb:
                    file_name = str(line[0])
                    in_project = False

                    if file_name.startswith(bugsnag_module_path):
                        continue

                    if file_name.startswith(configuration.library_root):
                        file_name = file_name[len(configuration.library_root):]
                    elif file_name.startswith(configuration.project_root):
                        file_name = file_name[len(configuration.project_root):]
                        in_project = True

                    stacktrace.append({
                        "file": file_name,
                        "lineNumber": int(str(line[1])),
                        "method": str(line[2]),
                        "inProject": in_project,
                    })

                stacktrace.reverse()

                bugsnag.notify(exc_type(exc_value), traceback=stacktrace)


