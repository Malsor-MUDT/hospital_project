from flask import Flask, app
from flask_sqlalchemy import SQLAlchemy
import json

db = SQLAlchemy()
def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    db.init_app(app)

    # Import and register blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.superadmin_routes import superadmin_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.main_routes import main_bp
    from app.routes.doctor_routes import doctor_bp
    
    app.register_blueprint(doctor_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(superadmin_bp)
    app.register_blueprint(admin_bp)
    
    # Register custom template filter - FIXED VERSION
    @app.template_filter('fromjson')
    def fromjson_filter(value):
        """Convert JSON string to Python object"""
        if not value:
            return {}
        if isinstance(value, dict):
            return value  # Already a dict
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # If it's already a string representation, try to handle it
                if value.startswith('{') or value.startswith('['):
                    # Try to clean and parse
                    try:
                        # Remove any problematic characters
                        cleaned = value.strip()
                        return json.loads(cleaned)
                    except:
                        return {}
                return {}
        return {}
    
    @app.template_filter('thousands')
    def thousands_filter(value):
        """Format number with thousands separators"""
        try:
            return f"{int(value):,}"
        except (ValueError, TypeError):
            return value
    
    return app