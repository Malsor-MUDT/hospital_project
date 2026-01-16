from app import db
from app.models.treatment import Treatment
from app.models.patient import Patient
from app.models.device import Device
from app.models.doctor import Doctor

class TreatmentSession(db.Model):
    __tablename__ = "treatment_sessions"

    session_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.patient_id"), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.hospital_id"), nullable=False)
    treatment_id = db.Column(db.Integer, db.ForeignKey("treatments.treatment_id"), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.device_id"), nullable=True)
    doctor_id = db.Column(db.String(36), db.ForeignKey("doctors.doctor_id"), nullable=True)
    nurse_id = db.Column(db.String(36), db.ForeignKey("nurses.nurse_id"), nullable=True)
    report_id = db.Column(db.String(36), db.ForeignKey("medical_reports.report_id"), nullable=True)
    doctor_minutes = db.Column(db.Integer, nullable=True)
    nurse_minutes = db.Column(db.Integer, nullable=True)
    device_cost = db.Column(db.Float, nullable=True)
    device_price = db.Column(db.Float, nullable=True)
    staff_cost = db.Column(db.Float, nullable=True)
    total_price = db.Column(db.Float, nullable=True)
    profit = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Relationships with unique backrefs
  # Relationships with logical unique names
    patient_session   = db.relationship("Patient", backref="sessions_for_patient")
    doctor_session    = db.relationship("Doctor", backref="sessions_for_doctor")
    device_session    = db.relationship("Device", backref="sessions_for_device")
    treatment_session = db.relationship("Treatment", backref="sessions_for_treatment")
