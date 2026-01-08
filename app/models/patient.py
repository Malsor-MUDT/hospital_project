from app import db

class Patient(db.Model):
    __tablename__ = "patients"

    patient_id = db.Column(db.String(36), primary_key=True)  # UUID
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.hospital_id"), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    dob = db.Column(db.Date, nullable=False)

    # Relationships
    treatment_sessions = db.relationship("TreatmentSession", backref="patient", lazy=True)
