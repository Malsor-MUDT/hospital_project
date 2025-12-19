from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    db.init_app(app)

    # Import and register blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.superadmin_routes import superadmin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(superadmin_bp)  # ✅ register superadmin blueprint

    return app
