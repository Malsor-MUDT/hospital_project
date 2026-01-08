from app import db

class TreatmentSession(db.Model):
    __tablename__ = "treatment_sessions"

    session_id = db.Column(db.String(36), primary_key=True)
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.patient_id"), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.hospital_id"), nullable=False)
    treatment_id = db.Column(db.Integer, db.ForeignKey("treatments.treatment_id"), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.device_id"), nullable=True)
    doctor_id = db.Column(db.String(36), db.ForeignKey("doctors.doctor_id"), nullable=True)
    nurse_id = db.Column(db.String(36), db.ForeignKey("nurses.nurse_id"), nullable=True)
    doctor_minutes = db.Column(db.Integer, nullable=True)
    nurse_minutes = db.Column(db.Integer, nullable=True)
    device_cost = db.Column(db.Float, nullable=True)
    device_price = db.Column(db.Float, nullable=True)
    staff_cost = db.Column(db.Float, nullable=True)
    total_price = db.Column(db.Float, nullable=True)
    profit = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
