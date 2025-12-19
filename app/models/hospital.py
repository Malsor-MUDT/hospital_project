from app import db

class Hospital(db.Model):
    __tablename__ = "hospitals"

    hospital_id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)

    # Optional, but useful
    admins = db.relationship(
        "Admin",
        backref="hospital",
        lazy=True
    )
