from werkzeug.security import check_password_hash
from app.models.admin import Admin

def authenticate_admin(email: str, password: str):
    admin = Admin.query.filter_by(email=email).first()

    if not admin:
        return None

    if not check_password_hash(admin.password, password):
        return None

    return admin
