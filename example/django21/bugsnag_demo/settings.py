"""
Django settings for bugsnag_demo project.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '3n3h7r@tpqnwqtt8#avxh_t75k_6zf3x)@6cg!u(&xmz79(26h'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)

MIDDLEWARE = (
    # make sure to add Bugsnag to the top of your middleware.
    'bugsnag.django.middleware.BugsnagMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
)

ROOT_URLCONF = 'bugsnag_demo.urls'

WSGI_APPLICATION = 'bugsnag_demo.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

# Initialize Bugsnag to begin tracking errors. Only an api key is required, but here are some other helpful configuration details:
BUGSNAG = {

    # get your own api key at bugsnag.com
    "api_key": "YOUR_API_KEY_HERE",

    # By default, requests are sent asynchronously. If you would like to block until the request is done, you can set to false.
    "asynchronous": False,

    # If you track deploys or session rates, make sure to set the correct version.
    "app_version": '1.2.3',

    # Defaults to false, this allows you to log each session which will be used to calculate crash rates in your dashboard for each release.
    "auto_capture_sessions": True,

    # Sets which exception classes should never be sent to Bugsnag.
    "ignore_classes": ['django.http.response.Http404', 'DontCare'],

    # Defines the release stage for all events that occur in this app.
    "release_stage": 'development',

    # Defines which release stages bugsnag should report. e.g. ignore staging errors.
    "notify_release_stages": [ 'development', 'production'],

    # Any param key that contains one of these strings will be filtered out of all error reports.
    "params_filters": ["credit_card_number", "password", "ssn"],

    # We mark stacktrace lines as inProject if they come from files inside root:
    # "project_root": "/path/to/your/project",

    # Useful if you are wrapping bugsnag.notify() in with your own library, to ensure errors group properly.
    # "traceback_exclude_module": [myapp.custom_logging],
}
