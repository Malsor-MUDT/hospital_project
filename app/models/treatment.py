from app import db

class Treatment(db.Model):
    __tablename__ = "treatments"

    treatment_id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.hospital_id"), nullable=False)

    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    requires_device = db.Column(db.Boolean, default=False)

    hospital = db.relationship("Hospital", backref="treatments")
