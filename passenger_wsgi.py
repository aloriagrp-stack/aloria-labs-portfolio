import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

try:
    from mobile_server import app
    from a2wsgi import ASGIMiddleware

    _wsgi_app = None
    _wsgi_pid = None

    def get_application():
        global _wsgi_app, _wsgi_pid
        current_pid = os.getpid()
        if _wsgi_app is None or _wsgi_pid != current_pid:
            _wsgi_pid = current_pid
            _wsgi_app = ASGIMiddleware(app)
        return _wsgi_app

    def application(environ, start_response):
        script_name = environ.get('SCRIPT_NAME', '')
        if script_name:
            environ['PATH_INFO'] = script_name + environ.get('PATH_INFO', '')
            environ['SCRIPT_NAME'] = ''
        return get_application()(environ, start_response)

except Exception as e:
    import traceback
    err_tb = traceback.format_exc()
    def application(environ, start_response):
        start_response('500 Internal Server Error', [('Content-Type', 'text/html; charset=utf-8')])
        return [f'<h1>Aloria Hunter Backend Startup Error</h1><pre>{err_tb}</pre>'.encode('utf-8')]
