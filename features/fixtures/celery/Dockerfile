ARG PYTHON_TEST_VERSION
FROM python:$PYTHON_TEST_VERSION

COPY app/ /usr/src/app
COPY temp-bugsnag-python/ /usr/src/bugsnag

WORKDIR /usr/src/app

ARG CELERY_TEST_VERSION
RUN CELERY_TEST_VERSION=$CELERY_TEST_VERSION pip install --no-cache-dir -r requirements.txt

CMD celery --app bugsnag_celery_test_app.main worker -l INFO
