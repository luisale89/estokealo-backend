from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from frontend_server import create_app as create_frontend
from landingpage_server import create_app as create_landing

application = DispatcherMiddleware(create_landing(), {
    '/app': create_frontend()
})

if __name__ == '__main__':
    run_simple(
        hostname='localhost',
        port=5000,
        application=application,
        use_reloader=True,
        use_debugger=True,
        use_evalex=True
    )