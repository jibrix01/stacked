import os

from app import app

if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG') == '1'
    app.run(
        debug=debug,
        use_reloader=False,
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        threaded=True,
    )
