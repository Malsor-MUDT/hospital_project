# app/models/data_transfer.py
from app import db
from datetime import datetime

class DataTransfer(db.Model):
    __tablename__ = "data_transfers"

    transfer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.patient_id"), nullable=False)
    source_hospital = db.Column(db.Integer, db.ForeignKey("hospitals.hospital_id"), nullable=False)
    target_hospital = db.Column(db.Integer, db.ForeignKey("hospitals.hospital_id"), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.department_id"), nullable=False)
    initiated_by_staff = db.Column(db.Integer, db.ForeignKey("admins.admin_id"), nullable=False)

    # optional, for future use
    checksum_original = db.Column(db.String(128), nullable=True)
    checksum_verified = db.Column(db.String(128), nullable=True)

    transfer_status = db.Column(db.Enum("pending","verified", "accepted","rejected", "failed"), default="pending", nullable=False)
    transferred_at = db.Column(db.DateTime, default=None, nullable=True)

    # relationships
    patient = db.relationship("Patient")
    source = db.relationship("Hospital", foreign_keys=[source_hospital])
    target = db.relationship("Hospital", foreign_keys=[target_hospital])
    department = db.relationship("Department")
