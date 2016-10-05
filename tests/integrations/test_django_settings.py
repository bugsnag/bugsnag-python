DATABASES = {
    'default': {
        'NAME': 'default.db',
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

SECRET_KEY = 'bugsnag_python_super_secret_key'

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django.contrib.sessions',
    'django.contrib.admin',
    'tests',
]

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'bugsnag.django.middleware.BugsnagMiddleware'
)
