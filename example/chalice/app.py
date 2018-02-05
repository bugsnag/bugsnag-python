import os
import logging

import bugsnag

from chalice import Chalice
from bugsnag.handlers import BugsnagHandler

bugsnag.configure(
    api_key = os.environ.get('BUGSNAG_API_KEY'),
    asynchronous = False,
    release_stage = os.environ.get('BUGSNAG_RELEASE_STAGE')
)

app = Chalice(app_name='chalice-example')

handler = BugsnagHandler()
app.log.addHandler(handler)

@app.route('/')
def index():
    return "Check out the `chalice/app.py` file to see what routes are available and how they're set up"

@app.route('/crash')
def crash():
    return 1/0

@app.route('/log')
def log():
    app.log.debug('Nothing went wrong')
    app.log.error('Something went wrong!')
    return "An error has been logged, but the debug has not"

@app.route('/notify')
def notify():
    bugsnag.notify(Exception("Nothing went wrong!"))
    return "Notified Bugsnag of an error"

@app.route('/metadata')
def callback():
    bugsnag.notify(
        Exception("Nothing went wrong!"),
        meta_data = {
            'Request info': {
                'route': 'metadata'
            },
            'Resolve info': {
                'status': 200,
                'message': 'Metadata has been added to this notification'
            }
        },
    )