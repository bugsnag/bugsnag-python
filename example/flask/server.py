from flask import Flask, request, render_template
from flaskext.markdown import Markdown
import bugsnag

# Import platform specific Bugsnag features
from bugsnag.flask import handle_exceptions

app = Flask(__name__)
Markdown(app)

# Configure Bugsnag
bugsnag.configure(
    api_key = '03c1b987da2ed0df8795cc4968b76185'
)

# Attach Bugsnag to flasks exception handler
handle_exceptions(app)

@app.route('/')
def index():
    return render_template('index.html')

# Will cause a ZeroDivisionError to be caught by the bugsnag exception handler
@app.route('/crashzero')
def crashzero():
    return 1/0

# Should cause a KeyError to be caught by the bugsnag exception handler
@app.route('/crashdict')
def crashdict():
    customheader = request.headers['my-custom-header']
    return 'Received your header: ' + customheader

# Will crash but attach diagnostic data through a callback function before reporting the error
@app.route('/crashcallback')
def crashcallback():
    bugsnag.before_notify(callback)
    raise(Exception('Flask demo: Everything is fine, check the Diagnostics tab at <a href=\"bugsnag.com\">bugsnag.com</a>'))

def callback(notification):
    if notification.context == 'GET /crashcallback':
        notification.add_tab('Diagnostics', {
            'message': 'Flask demo: Everything is fine',
            'status': 200
        })

# Will notify Bugsnag of an exception manually, which can be used to notify Bugsnag of handled errors
@app.route('/notify')
def notify():
    bugsnag.notify(Exception('Flask demo: Manual notification'))
    return 'The app hasn\'t crashed, but check <a href=\"bugsnag.com\">bugsnag.com</a> to view notifications'

# Will notify Bugsnag of an exception, with some metadata attached for better debugging
@app.route('/notifywithmetadata')
def notifywithmetadata():
    bugsnag.notify(
        Exception('Flask demo: Manual notification with metadata'),
        meta_data = {
            'Request info': {
                'route': 'notifywithmetadata',
                'headers': request.headers
            },
            'Resolve info': {
                'status': 200,
                'message': 'Metadata has been added to this notificaiton'
            }
        },
    )
    return ('Metadata was added to the notification, check <a href=\"bugsnag.com\">bugsnag.com</a> ' +
        ' to view on the "Request info" and "Resolve info" tabs')

# Will notify Bugsnag of an exception, and include a context included for grouping
@app.route('/notifywithcontext')
def notifywithcontext():
    bugsnag.notify(
        Exception('Flask demo: Manual notification with context'),
        context = 'notifywithcontext'
    )
    return 'The context was changed to notifywithcontext for better grouping'

# Will notify Bugsnag of an exception, with a defined severity for different handling
@app.route('/notifywithseverity')
def notifywithseverity():
    bugsnag.notify(
        Exception('Flask demo: Manual notificaiton with severity'),
        severity = 'info',
    )
    return 'The severity was set to info, check <a href=\"bugsnag.com\">bugsnag.com</a> to see the difference'

if __name__ == '__main__':
    app.run(port=3000)
