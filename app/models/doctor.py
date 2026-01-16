from app import db

class Doctor(db.Model):
    __tablename__ = "doctors"

    doctor_id = db.Column(db.String(36), primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.hospital_id"), nullable=False)
    specialization_id = db.Column(db.Integer, db.ForeignKey("specializations.specialization_id"), nullable=False)

    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    hourly_wage = db.Column(db.Numeric(8,2), default=0.00)
    hours_per_month = db.Column(db.Integer, default=160)

    specialization = db.relationship("Specialization", backref="doctors")
