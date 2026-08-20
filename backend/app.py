from flask import Flask, render_template

from routes.dashboard import dashboard_bp
from routes.insights import insights_bp
from routes.predict import predict_bp


def create_app():
    app = Flask(__name__)

    app.register_blueprint(predict_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(insights_bp)

    @app.route('/')
    def home():
        return render_template('insights.html')

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
