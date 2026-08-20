import os

from app import app

if __name__ == '__main__':
    # The Werkzeug auto-reloader (the default when debug=True) works by
    # re-executing this process under a file-watcher. In sandboxed /
    # containerized environments without a usable inotify backend, that
    # re-exec hangs forever during startup: the process never finishes
    # binding the socket, so every request -- dashboard, predict, all of
    # it -- just times out with no error printed. That's almost certainly
    # what "the app doesn't work" was: it never actually came up.
    #
    # Debug mode (better tracebacks, auto-reload on save) is still
    # available for local development -- just opt in explicitly, and
    # only the reloader is disabled by default:
    #   FLASK_DEBUG=1 python run.py
    debug = os.environ.get('FLASK_DEBUG') == '1'
    app.run(
        debug=debug,
        use_reloader=False,
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        threaded=True,
    )
