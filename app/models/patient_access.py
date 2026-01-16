from app import db
from datetime import datetime

class PatientAccess(db.Model):
    __tablename__ = "patient_access"

    access_id = db.Column(db.Integer, primary_key=True)

    patient_id = db.Column(
        db.String(36),   # UUID
        db.ForeignKey("patients.patient_id"),
        nullable=False
    )

    hospital_id = db.Column(
        db.Integer,
        db.ForeignKey("hospitals.hospital_id"),
        nullable=False
    )

    access_reason = db.Column(
        db.String(255),
        nullable=False
    )

    transfer_id = db.Column(
        db.Integer,
        db.ForeignKey("data_transfers.transfer_id"),
        nullable=True
    )

    access_granted_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    is_active = db.Column(
        db.Boolean,
        default=True
    )

    # -----------------------
    # Relationships
    # -----------------------

    patient = db.relationship(
        "Patient",
        backref=db.backref("access_entries", lazy=True)
    )

    hospital = db.relationship(
        "Hospital",
        backref=db.backref("patient_accesses", lazy=True)
    )

    transfer = db.relationship(
        "DataTransfer", lazy=True
    )
