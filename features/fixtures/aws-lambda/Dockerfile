ARG PYTHON_TEST_VERSION
FROM python:$PYTHON_TEST_VERSION

# install the SAM CLI
ENV SAM_CLI_TELEMETRY=0
RUN pip install --upgrade pip && pip install aws-sam-cli

COPY temp-bugsnag-python/ /usr/src/bugsnag

WORKDIR /usr/src/app
