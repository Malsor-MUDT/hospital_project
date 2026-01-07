from app import db

class Nurse(db.Model):
    __tablename__ = "nurses"

    nurse_id = db.Column(db.String(36), primary_key=True)  # UUID
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.hospital_id"), nullable=False)

    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    hourly_wage = db.Column(db.Numeric(8, 2), nullable=False)
    hours_per_month = db.Column(db.Integer, nullable=False, default=160)

