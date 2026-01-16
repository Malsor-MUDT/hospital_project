from flask import Blueprint, render_template, session,request, redirect, url_for, flash
from app import db
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.treatment_session import TreatmentSession
from app.models.treatment import Treatment
from app.models.medical_report import MedicalReport
from app.models.device import Device
import uuid


doctor_bp = Blueprint("doctor", __name__, url_prefix="/doctor")

# ----------------------
# Doctor Dashboard
# ----------------------
@doctor_bp.route("/debug_routes")
def debug_routes():
    return "<br>".join([str(rule) for rule in app.url_map.iter_rules()])

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

    patients = Patient.query.filter_by(
        hospital_id=session.get("hospital_id")
    ).all()

    return render_template(
        "dashboards/doctor/patients.html",
        patients=patients
    )

@doctor_bp.route("/patients/<patient_id>/start")
def start_exam(patient_id):
    if "doctor_id" not in session:
        flash("Please log in first", "danger")
        return redirect(url_for("auth.doctor_login"))

    patient = Patient.query.filter_by(
        patient_id=patient_id,
        hospital_id=session.get("hospital_id")
    ).first_or_404()

    return render_template(
        "dashboards/doctor/start_exam.html",
        patient=patient
    )

@doctor_bp.route("/reports")
def reports():
    if "doctor_id" not in session:
        flash("Please log in first", "danger")
        return redirect(url_for("auth.doctor_login"))

    doctor_id = session["doctor_id"]
    reports = MedicalReport.query.filter_by(doctor_id=doctor_id).order_by(MedicalReport.created_at.desc()).all()

    return render_template(
        "dashboards/doctor/medical_reports.html",
        reports=reports
    )


@doctor_bp.route("/patients/<patient_id>/report", methods=["POST"])
def submit_report(patient_id):
    if "doctor_id" not in session:
        flash("Please log in first", "danger")
        return redirect(url_for("auth.doctor_login"))

    report = MedicalReport(
        report_id=str(uuid.uuid4()),
        patient_id=patient_id,
        hospital_id=session["hospital_id"],
        doctor_id=session["doctor_id"],
        symptoms=request.form.get("symptoms"),
        diagnosis=request.form.get("diagnosis"),
        notes=request.form.get("notes"),
        treatment_required=bool(int(request.form.get("treatment_required")))
    )

    db.session.add(report)
    db.session.commit()

    if report.treatment_required:
        return redirect(url_for("doctor.select_treatment", report_id=report.report_id))

    flash("Medical report saved successfully.", "success")
    return redirect(url_for("doctor.dashboard"))


@doctor_bp.route("/reports/<report_id>/treatment", methods=["GET", "POST"])
def select_treatment(report_id):
    if "doctor_id" not in session:
        flash("Please log in first", "danger")
        return redirect(url_for("auth.doctor_login"))

    # Get the report
    report = MedicalReport.query.get_or_404(report_id)

    # All treatments for the hospital
    treatments = Treatment.query.filter_by(hospital_id=report.hospital_id).all()
    devices = Device.query.filter_by(hospital_id=report.hospital_id).all()

    if request.method == "POST":
        treatment_id = request.form.get("treatment_id")
        notes = request.form.get("notes")

        # Get the selected treatment
        treatment = Treatment.query.get_or_404(treatment_id)
        

        # Check if this treatment requires a device
        if treatment.requires_device:
            device_id = request.form.get("device_id")
            if not device_id:
                flash("Please select a device for this treatment.", "danger")
                return redirect(url_for("doctor.select_treatment", report_id=report_id))

            # Get the selected device
            device = Device.query.get_or_404(device_id)

            # Snapshot of device values
            doctor_minutes = device.doctor_minutes
            nurse_minutes = device.nurse_minutes
            staff_cost = (float(device.doctor_hourly_wage) / 60) * doctor_minutes \
                       + (float(device.nurse_hourly_wage) / 60) * nurse_minutes
            device_cost = float(device.cost_per_use)  # includes staff
            device_price = float(device.price_per_use)
            total_price = device_price
            profit = total_price - device_cost
            device_id_value = device.device_id
        else:
            # No device required → all device-related fields NULL
            doctor_minutes = None
            nurse_minutes = None
            staff_cost = None
            device_cost = None
            device_price = None
            total_price = None
            profit = None
            device_id_value = None

        # Create treatment session
        session_obj = TreatmentSession(
            patient_id=report.patient_id,
            hospital_id=report.hospital_id,
            treatment_id=treatment_id,
            device_id=device_id_value,
            doctor_id=session["doctor_id"],
            report_id=report.report_id,
            doctor_minutes=doctor_minutes,
            nurse_minutes=nurse_minutes,
            staff_cost=staff_cost,
            device_cost=device_cost,
            device_price=device_price,
            total_price=total_price,
            profit=profit,
            notes=notes
        )

        db.session.add(session_obj)
        db.session.commit()

        flash("Treatment assigned successfully.", "success")
        # Go back to patient's page or dashboard
        return redirect(url_for("doctor.patients"))

    # GET request → show the form
    return render_template(
        "dashboards/doctor/select_treatment.html",
        report=report,
        treatments=treatments,
        devices=devices
    )





@doctor_bp.route("/treatment_sessions")
def treatment_sessions():
    if "doctor_id" not in session:
        flash("Please log in first", "danger")
        return redirect(url_for("auth.doctor_login"))

    doctor = Doctor.query.get(session["doctor_id"])
    sessions = TreatmentSession.query.filter_by(hospital_id=doctor.hospital_id).order_by(TreatmentSession.created_at.desc()).all()

    return render_template("dashboards/doctor/treatment_sessions.html", sessions=sessions)

