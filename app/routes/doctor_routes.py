from flask import Blueprint, render_template, session, redirect, url_for, flash
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.treatment_session import TreatmentSession

doctor_bp = Blueprint("doctor", __name__, url_prefix="/doctor")

# ----------------------
# Doctor Dashboard
# ----------------------
@doctor_bp.route("/dashboard")
def dashboard():
    if "doctor_id" not in session:
        flash("Please log in first", "danger")
        return redirect(url_for("auth.doctor_login"))
    
    doctor_id = session.get("doctor_id")
    doctor = Doctor.query.get(doctor_id)
    patients = Patient.query.filter_by(hospital_id=doctor.hospital_id).all()
    sessions = TreatmentSession.query.filter_by(hospital_id=doctor.hospital_id).all()

    return render_template("dashboards/doctor/doctor_dashboard.html",
                           doctor=doctor,
                           patients=patients,
                           sessions=sessions)

@doctor_bp.route("/patients")
def patients():
    if "doctor_id" not in session:
        flash("Please log in first", "danger")
        return redirect(url_for("auth.doctor_login"))

    doctor = Doctor.query.get(session["doctor_id"])
    patients_list = Patient.query.filter_by(hospital_id=doctor.hospital_id).all()
    return render_template("dashboards/doctor/patients.html", patients=patients_list)


@doctor_bp.route("/treatment_sessions")
def treatment_sessions():
    doctor = Doctor.query.get(session["doctor_id"])
    sessions = TreatmentSession.query.filter_by(hospital_id=doctor.hospital_id).all()
    return render_template("dashboards/doctor/treatment_sessions.html", sessions=sessions)
