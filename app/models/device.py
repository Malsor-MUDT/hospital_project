from app import db

class Device(db.Model):
    __tablename__ = "devices"

    device_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    hospital_id = db.Column(
        db.Integer,
        db.ForeignKey("hospitals.hospital_id"),
        nullable=False
    )

    device_type = db.Column(db.String(100), nullable=False)

    # Cost model inputs
    base_machine_cost = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    doctor_minutes = db.Column(db.Integer, nullable=False, default=0)
    doctor_hourly_wage = db.Column(db.Numeric(8, 2), nullable=False, default=0)
    nurse_minutes = db.Column(db.Integer, nullable=False, default=0)
    nurse_hourly_wage = db.Column(db.Numeric(8, 2), nullable=False, default=0)

    # Final values
    cost_per_use = db.Column(db.Numeric(8, 2), nullable=False)
    price_per_use = db.Column(db.Numeric(8, 2), nullable=False)
    
    hospital = db.relationship(
        "Hospital",
        backref=db.backref("devices", lazy=True)
    )

    status = db.Column(
        db.Enum("operational", "maintenance", "broken"),
        nullable=False,
        default="operational"
    )
