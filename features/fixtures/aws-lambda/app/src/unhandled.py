import os
import json
import bugsnag


bugsnag.configure(
    api_key=os.environ["BUGSNAG_API_KEY"],
    endpoint=os.environ["BUGSNAG_ERROR_ENDPOINT"],
    session_endpoint=os.environ["BUGSNAG_SESSION_ENDPOINT"],
)


@bugsnag.aws_lambda_handler
def handler(event, context):
    raise Exception("uh oh!")
