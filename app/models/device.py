from app import db

class Device(db.Model):
    __tablename__ = "devices"

    device_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    hospital_id = db.Column(
        db.Integer,
        db.ForeignKey("hospitals.hospital_id"),
        nullable=False
    )

    device_type = db.Column(
        db.String(100),
        nullable=False
    )

    cost_per_use = db.Column(
        db.Numeric(8, 2),
        nullable=False
    )
    price_per_use = db.Column(
        db.Numeric(8, 2),
        nullable=False
    )
    status = db.Column(
        db.Enum("operational", "maintenance", "broken"),
        nullable=False,
        default="operational"
    )
