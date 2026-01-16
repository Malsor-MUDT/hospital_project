# app/models/hospital_connection.py
from app import db

class HospitalConnection(db.Model):
    __tablename__ = "hospital_connections"

    connection_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    hospital_from = db.Column(
        db.Integer,
        db.ForeignKey("hospitals.hospital_id"),
        nullable=False
    )
    hospital_to = db.Column(
        db.Integer,
        db.ForeignKey("hospitals.hospital_id"),
        nullable=False
    )
   
    transfer_cost = db.Column(db.Float, nullable=False)
    latency_minutes = db.Column(db.Float, nullable=False)
    reliability = db.Column(db.Float, nullable=False)

    created_at = db.Column(db.DateTime, server_default=db.func.now())

    from_hospital = db.relationship(
            "Hospital",
            foreign_keys=[hospital_from],
            backref="connections_from"
        )

    to_hospital = db.relationship(
            "Hospital",
            foreign_keys=[hospital_to],
            backref="connections_to"
        )