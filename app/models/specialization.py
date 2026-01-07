from app import db

class Specialization(db.Model):
    __tablename__ = "specializations"

    specialization_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.department_id"), nullable=False)
    name = db.Column(db.String(150), nullable=False)

    # Relationship to department (optional but useful)
    department = db.relationship("Department", backref="specializations", lazy=True)
