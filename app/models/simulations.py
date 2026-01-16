from app import db
from datetime import datetime
class Simulation(db.Model):
    __tablename__ = "simulations"
    
    simulation_id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.hospital_id"), nullable=False)
    simulation_date = db.Column(db.DateTime, default=datetime.utcnow)
    simulation_type = db.Column(db.String(50))  # 'revenue_forecast', 'price_optimization', etc.
    parameters = db.Column(db.JSON)  # Stores all input parameters
    results = db.Column(db.JSON)  # Stores simulation results
    recommendations = db.Column(db.Text)
    
    hospital = db.relationship("Hospital", backref="simulations")