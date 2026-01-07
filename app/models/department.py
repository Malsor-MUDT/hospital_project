from app import db

class Department(db.Model):
    __tablename__ = "departments"

    department_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.hospital_id"), nullable=False)
    name = db.Column(db.String(150), nullable=False)

    # Relationship to hospital (optional, useful)
    hospital = db.relationship("Hospital", backref="departments", lazy=True)
