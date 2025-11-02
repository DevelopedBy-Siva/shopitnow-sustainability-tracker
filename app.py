from flask import Flask
from config import Config
from models import db
from routes.carbon import carbon_bp
from routes.user_tracking import user_bp
from routes.recommend import recommend_bp
from routes.summary import summary_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    app.register_blueprint(carbon_bp, url_prefix="/api/sustainability")
    app.register_blueprint(user_bp, url_prefix="/api/sustainability")
    app.register_blueprint(recommend_bp, url_prefix="/api/sustainability")
    app.register_blueprint(summary_bp, url_prefix="/api/sustainability")
    return app


app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5001, debug=True)
