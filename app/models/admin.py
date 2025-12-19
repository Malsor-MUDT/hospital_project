from app import db

class Admin(db.Model):
    __tablename__ = "admins"

    admin_id = db.Column(db.String(36), primary_key=True)

    hospital_id = db.Column(
        db.String(36),
        db.ForeignKey("hospitals.hospital_id"),
        nullable=True  # REQUIRED for superadmin
    )

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False,
        index=True
    )

    password = db.Column(db.String(255), nullable=False)

    role = db.Column(
        db.Integer,
        nullable=False
    )  # 0 = admin, 1 = superadmin
