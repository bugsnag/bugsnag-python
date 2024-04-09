import os
import json
import bugsnag


bugsnag.configure(
    api_key=os.environ["BUGSNAG_API_KEY"],
    endpoint=os.environ["BUGSNAG_ERROR_ENDPOINT"],
    session_endpoint=os.environ["BUGSNAG_SESSION_ENDPOINT"],
    auto_notify=False,
)


@bugsnag.aws_lambda_handler
def handler(event, context):
    bugsnag.notify(Exception("hi friend"))

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Did not crash!",
        }),
    }
