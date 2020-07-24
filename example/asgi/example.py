import bugsnag
from bugsnag.asgi import BugsnagMiddleware

bugsnag.configure(api_key="YOUR-API-KEY-HERE")

async def broken_code():
    raise Exception('ASGI demo: This is an exception from async code')

async def app(scope, receive, send):
    await send({
        'type': 'http.response.start',
        'status': 200,
        'headers': [
            [b'content-type', b'text/plain'],
        ]
    })
    await broken_code()
    await send({
        'type': 'http.response.body',
        'body': b'Hello, world!',
    })

app = BugsnagMiddleware(app)
