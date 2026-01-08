from flask import Flask, app
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    db.init_app(app)

    # Import and register blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.superadmin_routes import superadmin_bp
    from app.routes.admin_routes import admin_bp
    # after importing auth_bp and superadmin_bp
    from app.routes.main_routes import main_bp
    from app.routes.doctor_routes import doctor_bp
    
    app.register_blueprint(doctor_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(superadmin_bp)
    app.register_blueprint(admin_bp) 

    return app
