from flask import Flask

class ReverseProxied(object):
    '''Wrap the application in this middleware and configure the 
    front-end server to add these headers, to let you quietly bind 
    this to a URL other than / and to an HTTP scheme that is 
    different than what is used locally.

    In nginx:
    location /myprefix {
        proxy_pass http://192.168.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Scheme $scheme;
        proxy_set_header X-Script-Name /myprefix;
        }

    :param app: the WSGI application
    '''
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        script_name = '/monitoring'
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]

        scheme = environ.get('HTTP_X_SCHEME', '')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        return self.app(environ, start_response)

app = Flask(__name__)

app.config.from_envvar('WEBSITE_SETTINGS', silent=False)

# try to configure logging. It is extremely difficult to figure out what the
# proper way to log exceptions from Flask when running under gunicorn is. I
# initially tried the solution here:
# https://stackoverflow.com/questions/14037975/how-do-i-write-flasks-excellent-debug-log-message-to-a-file-in-production
# however I kept getting permission denied errors when trying to open the file
# even though I had set up the correct permissions on /var/log/minard.
# Eventually I started looking for another way to do it and found this post:
# https://medium.com/@trstringer/logging-flask-and-gunicorn-the-manageable-way-2e6f0b8beb2f
# which discusses how to pipe Flask's messages to the gunicorn logger.
@app.before_first_request
def setup_logging():
    if not app.debug:
        import logging
        gunicorn_logger = logging.getLogger('gunicorn.error')
        for handler in gunicorn_logger.handlers:
            app.logger.addHandler(handler)

app.wsgi_app = ReverseProxied(app.wsgi_app)

import website.views
