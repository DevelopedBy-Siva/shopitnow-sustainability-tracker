from flask import Flask
from flask_cors import CORS
from config import Config
from models import db
from routes.recommend import recommend_bp
from routes.insight import insight_bp
from routes.cart import cart_bp
import os


def is_dev():
    env = os.getenv("APP_ENV", "production")
    if env == "development":
        return True
    return False


def create_app():
    app = Flask(__name__)
    CORS(
        app,
        resources={
            r"/*": {
                "origins": "*" if is_dev() else "https://shopit-now-client.vercel.app"
            }
        },
    )
    app.config.from_object(Config)
    db.init_app(app)
    app.register_blueprint(recommend_bp, url_prefix="/api/sustainability")
    app.register_blueprint(insight_bp, url_prefix="/api/sustainability")
    app.register_blueprint(cart_bp, url_prefix="/api/sustainability")
    return app


app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    if is_dev():
        app.run(host="0.0.0.0", port=5001, debug=True)
    else:
        from waitress import serve

        serve(app)
