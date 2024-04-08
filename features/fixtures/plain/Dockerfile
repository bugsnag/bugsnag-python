ARG PYTHON_TEST_VERSION
FROM python:$PYTHON_TEST_VERSION

COPY app/ /usr/src/app
COPY temp-bugsnag-python/ /usr/src/bugsnag

WORKDIR /usr/src/app

RUN pip install --no-cache-dir -r requirements.txt
