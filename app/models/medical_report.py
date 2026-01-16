from app import db

class MedicalReport(db.Model):
    __tablename__ = "medical_reports"

    report_id = db.Column(db.String(36), primary_key=True)
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.patient_id"), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.hospital_id"), nullable=False)
    doctor_id = db.Column(db.String(36), db.ForeignKey("doctors.doctor_id"), nullable=False)

    symptoms = db.Column(db.Text, nullable=False)
    diagnosis = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text)

    treatment_required = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    patient=db.relationship("Patient", backref="medical_reports")
