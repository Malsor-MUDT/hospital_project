from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from werkzeug.security import generate_password_hash
from app.models.device import Device
from app.models.nurse import Nurse
from app.models.specialization import Specialization
from app.models.department import Department
from app.models.doctor import Doctor
from app.models.treatment import Treatment
from app.models.patient import Patient
from app.models.admin import Admin
import uuid

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/dashboard")
def dashboard():
    # Only normal admins (role = 0)
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    return render_template("dashboards/admin/admin_dashboard.html")


@admin_bp.route("/devices")
def devices():
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    admin = Admin.query.get(session["admin_id"])

    devices = Device.query.filter_by(
        hospital_id=admin.hospital_id
    ).all()

    return render_template(
        "dashboards/admin/devices.html",
        devices=devices
    )


# ----------------------
# Devices – Add
# ----------------------
@admin_bp.route("/devices/add", methods=["POST"])
def add_device():
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    admin = Admin.query.get(session["admin_id"])

    new_device = Device(
        device_id=str(uuid.uuid4()),
        hospital_id=admin.hospital_id,
        device_type=request.form.get("device_type"),
        cost_per_use=request.form.get("cost_per_use"),
        price_per_use=request.form.get("price_per_use"),
        status=request.form.get("status"),
    )

    db.session.add(new_device)
    db.session.commit()

    flash("Device added successfully", "success")
    return redirect(url_for("admin.devices"))

@admin_bp.route("/devices/update/<int:device_id>", methods=["POST"])
def update_device(device_id):
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    device = Device.query.filter_by(
        device_id=device_id,
        hospital_id=session.get("hospital_id")
    ).first_or_404()

    device.device_type = request.form.get("device_type")
    device.cost_per_use = request.form.get("cost_per_use")
    device.price_per_use = request.form.get("price_per_use")
    device.status = request.form.get("status")

    db.session.commit()

    flash("Device updated successfully", "success")
    return redirect(url_for("admin.devices"))


# -----------------------
# Delete Device
# -----------------------
@admin_bp.route("/devices/delete/<int:device_id>", methods=["POST"])
def delete_device(device_id):
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    device = Device.query.filter_by(
        device_id=device_id,
        hospital_id=session.get("hospital_id")
    ).first_or_404()

    db.session.delete(device)
    db.session.commit()

    flash("Device deleted", "success")
    return redirect(url_for("admin.devices"))


@admin_bp.route("/nurses")
def nurses():
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    hospital_id = session.get("hospital_id")

    nurses = Nurse.query.filter_by(hospital_id=hospital_id).all()
    return render_template(
        "dashboards/admin/nurses.html",
        nurses=nurses
    )

@admin_bp.route("/nurses/add", methods=["POST"])
def add_nurse():
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    nurse = Nurse(
        nurse_id=str(uuid.uuid4()),
        hospital_id=session.get("hospital_id"),
        name=request.form.get("name"),
        email=request.form.get("email"),
        hourly_wage=request.form.get("hourly_wage"),
        hours_per_month=request.form.get("hours_per_month"),
        password=generate_password_hash(request.form.get("password"))
    )

    db.session.add(nurse)
    db.session.commit()

    flash("Nurse added successfully", "success")
    return redirect(url_for("admin.nurses"))

@admin_bp.route("/nurses/update/<string:nurse_id>", methods=["POST"])
def update_nurse(nurse_id):
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    nurse = Nurse.query.get_or_404(nurse_id)

    # Optional safety check
    if nurse.hospital_id != session.get("hospital_id"):
        flash("Unauthorized action", "danger")
        return redirect(url_for("admin.nurses"))

    nurse.name = request.form.get("name")
    nurse.email = request.form.get("email")
    nurse.hourly_wage = request.form.get("hourly_wage")
    nurse.hours_per_month = request.form.get("hours_per_month")

    if request.form.get("password"):
        nurse.password = generate_password_hash(request.form.get("password"))

    db.session.commit()
    flash("Nurse updated successfully", "success")
    return redirect(url_for("admin.nurses"))

@admin_bp.route("/nurses/delete/<string:nurse_id>", methods=["POST"])
def delete_nurse(nurse_id):
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    nurse = Nurse.query.get_or_404(nurse_id)

    if nurse.hospital_id != session.get("hospital_id"):
        flash("Unauthorized action", "danger")
        return redirect(url_for("admin.nurses"))

    db.session.delete(nurse)
    db.session.commit()

    flash("Nurse deleted successfully", "success")
    return redirect(url_for("admin.nurses"))


@admin_bp.route("/departments")
def departments():
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    # Get all departments for this hospital
    hospital_id = session.get("hospital_id")
    departments = Department.query.filter_by(hospital_id=hospital_id).all()
    return render_template("dashboards/admin/departments.html", departments=departments)


# ----------------------
# Add Department
# ----------------------
@admin_bp.route("/departments/add", methods=["POST"])
def add_department():
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    hospital_id = session.get("hospital_id")
    name = request.form.get("name")

    department = Department(name=name, hospital_id=hospital_id)
    db.session.add(department)
    db.session.commit()

    flash("Department added successfully!", "success")
    return redirect(url_for("admin.departments"))


# ----------------------
# Update Department
# ----------------------
@admin_bp.route("/departments/update/<int:department_id>", methods=["POST"])
def update_department(department_id):
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    department = Department.query.get_or_404(department_id)
    department.name = request.form.get("name")
    db.session.commit()

    flash("Department updated successfully!", "success")
    return redirect(url_for("admin.departments"))


# ----------------------
# Delete Department
# ----------------------
@admin_bp.route("/departments/delete/<int:department_id>", methods=["POST"])
def delete_department(department_id):
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    department = Department.query.get_or_404(department_id)
    db.session.delete(department)
    db.session.commit()

    flash("Department deleted successfully!", "success")
    return redirect(url_for("admin.departments"))


@admin_bp.route("/specializations")
def specializations():
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    hospital_id = session.get("hospital_id")
    # Get all departments for this hospital
    departments = Department.query.filter_by(hospital_id=hospital_id).all()
    # Get all specializations in these departments
    specializations = Specialization.query.join(Department).filter(Department.hospital_id==hospital_id).all()
    return render_template("dashboards/admin/specializations.html", specializations=specializations, departments=departments)


# ----------------------
# Add Specialization
# ----------------------
@admin_bp.route("/specializations/add", methods=["POST"])
def add_specialization():
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    name = request.form.get("name")
    department_id = request.form.get("department_id")

    specialization = Specialization(name=name, department_id=department_id)
    db.session.add(specialization)
    db.session.commit()

    flash("Specialization added successfully!", "success")
    return redirect(url_for("admin.specializations"))


# ----------------------
# Update Specialization
# ----------------------
@admin_bp.route("/specializations/update/<int:specialization_id>", methods=["POST"])
def update_specialization(specialization_id):
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    specialization = Specialization.query.get_or_404(specialization_id)
    specialization.name = request.form.get("name")
    specialization.department_id = request.form.get("department_id")
    db.session.commit()

    flash("Specialization updated successfully!", "success")
    return redirect(url_for("admin.specializations"))


# ----------------------
# Delete Specialization
# ----------------------
@admin_bp.route("/specializations/delete/<int:specialization_id>", methods=["POST"])
def delete_specialization(specialization_id):
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    specialization = Specialization.query.get_or_404(specialization_id)
    db.session.delete(specialization)
    db.session.commit()

    flash("Specialization deleted successfully!", "success")
    return redirect(url_for("admin.specializations"))

@admin_bp.route("/doctors")
def doctors():
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    hospital_id = session.get("hospital_id")

    doctors = Doctor.query.filter_by(hospital_id=hospital_id).all()
    departments = Department.query.filter_by(hospital_id=hospital_id).all()

    return render_template(
        "dashboards/admin/doctors.html",
        doctors=doctors,
        departments=departments
    )

@admin_bp.route("/doctors/add", methods=["POST"])
def add_doctor():
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    # ❗ Prevent duplicate email
    if Doctor.query.filter_by(email=request.form.get("email")).first():
        flash("Doctor with this email already exists", "danger")
        return redirect(url_for("admin.doctors"))

    doctor = Doctor(
        doctor_id=str(uuid.uuid4()),
        hospital_id=session.get("hospital_id"),
        specialization_id=request.form.get("specialization_id"),
        name=request.form.get("name"),
        email=request.form.get("email"),
        password=generate_password_hash(request.form.get("password"))
    )

    db.session.add(doctor)
    db.session.commit()

    flash("Doctor added successfully", "success")
    return redirect(url_for("admin.doctors"))

@admin_bp.route("/doctors/update/<doctor_id>", methods=["POST"])
def update_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)

    doctor.name = request.form.get("name")
    doctor.specialization_id = request.form.get("specialization_id")

    db.session.commit()
    flash("Doctor updated", "success")
    return redirect(url_for("admin.doctors"))

@admin_bp.route("/doctors/delete/<doctor_id>", methods=["POST"])
def delete_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)

    db.session.delete(doctor)
    db.session.commit()

    flash("Doctor deleted", "success")
    return redirect(url_for("admin.doctors"))

@admin_bp.route("/specializations/by-department/<int:department_id>")
def specializations_by_department(department_id):
    specs = Specialization.query.filter_by(department_id=department_id).all()

    return {
        "specializations": [
            {"id": s.specialization_id, "name": s.name}
            for s in specs
        ]
    }


@admin_bp.route("/treatments")
def treatments():
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    treatments = Treatment.query.filter_by(
        hospital_id=session.get("hospital_id")
    ).all()

    return render_template(
        "dashboards/admin/treatments.html",
        treatments=treatments
    )

@admin_bp.route("/treatments/add", methods=["POST"])
def add_treatment():
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    treatment = Treatment(
        hospital_id=session["hospital_id"],
        name=request.form.get("name"),
        description=request.form.get("description"),
        requires_device=bool(request.form.get("requires_device"))
    )

    db.session.add(treatment)
    db.session.commit()

    flash("Treatment added successfully", "success")
    return redirect(url_for("admin.treatments"))

@admin_bp.route("/treatments/<int:treatment_id>/update", methods=["POST"])
def update_treatment(treatment_id):
    treatment = Treatment.query.get_or_404(treatment_id)

    treatment.name = request.form.get("name")
    treatment.description = request.form.get("description")
    treatment.requires_device = bool(request.form.get("requires_device"))

    db.session.commit()

    flash("Treatment updated", "success")
    return redirect(url_for("admin.treatments"))


@admin_bp.route("/treatments/<int:treatment_id>/delete", methods=["POST"])
def delete_treatment(treatment_id):
    treatment = Treatment.query.get_or_404(treatment_id)

    db.session.delete(treatment)
    db.session.commit()

    flash("Treatment deleted", "success")
    return redirect(url_for("admin.treatments"))

@admin_bp.route("/patients")
def patients():
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    patients_list = Patient.query.filter_by(hospital_id=session.get("hospital_id")).all()
    return render_template("dashboards/admin/patients.html", patients=patients_list)

# ----------------------
# Add Patient
# ----------------------
@admin_bp.route("/patients/add", methods=["POST"])
def add_patient():
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    patient = Patient(
        patient_id=str(uuid.uuid4()),
        hospital_id=session.get("hospital_id"),
        name=request.form.get("name"),
        email=request.form.get("email"),
        dob=request.form.get("dob")
    )
    db.session.add(patient)
    db.session.commit()

    flash("Patient added successfully", "success")
    return redirect(url_for("admin.patients"))

# ----------------------
# Update Patient
# ----------------------
@admin_bp.route("/patients/update/<patient_id>", methods=["POST"])
def update_patient(patient_id):
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    patient = Patient.query.get_or_404(patient_id)
    patient.name = request.form.get("name")
    patient.email = request.form.get("email")
    patient.dob = request.form.get("dob")
    db.session.commit()

    flash("Patient updated successfully", "success")
    return redirect(url_for("admin.patients"))

# ----------------------
# Delete Patient
# ----------------------
@admin_bp.route("/patients/delete/<patient_id>", methods=["POST"])
def delete_patient(patient_id):
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    patient = Patient.query.get_or_404(patient_id)
    db.session.delete(patient)
    db.session.commit()

    flash("Patient deleted successfully", "success")
    return redirect(url_for("admin.patients"))