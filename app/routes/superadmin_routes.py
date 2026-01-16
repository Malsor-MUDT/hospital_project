# app/routes/superadmin_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from app.models.hospital import Hospital
from app.models.admin import Admin
from app.models.hospital_connection import HospitalConnection
from werkzeug.security import generate_password_hash
import uuid

# Create the blueprint
superadmin_bp = Blueprint("superadmin", __name__, url_prefix="/superadmin")

# ----------------------
# Dashboard
# ----------------------
@superadmin_bp.route("/dashboard")
def dashboard():
    print("SESSION AT DASHBOARD:", dict(session))
    # Only superadmin role can access
    if session.get("role") != 1:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    hospitals = Hospital.query.all()
    admins = Admin.query.all()
    return render_template("dashboards/superadmin/superadmin_dashboard.html", hospitals=hospitals, admins=admins)

# ----------------------
# Add Hospital
# ----------------------
@superadmin_bp.route("/add_hospital", methods=["POST"])
def add_hospital():
    if session.get("role") != 1:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    name = request.form.get("name")
    location = request.form.get("location")
    hospital_id = str(uuid.uuid4())

    new_hospital = Hospital(hospital_id=hospital_id, name=name, location=location)
    db.session.add(new_hospital)
    db.session.commit()
    flash("Hospital added successfully!", "success")
    return redirect(url_for("superadmin.dashboard"))

# ----------------------
# Add Admin
# ----------------------
@superadmin_bp.route("/add_admin", methods=["POST"])
def add_admin():
    if session.get("role") != 1:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    name = request.form.get("name")
    email = request.form.get("email")
    password = generate_password_hash(request.form.get("password"))
    hospital_id = request.form.get("hospital_id")
    role = 0  # normal admin
    admin_id = str(uuid.uuid4())

    new_admin = Admin(admin_id=admin_id, hospital_id=hospital_id, name=name, email=email, password=password, role=role)
    db.session.add(new_admin)
    db.session.commit()
    flash("Admin added successfully!", "success")
    return redirect(url_for("superadmin.dashboard"))

# ----------------------
@superadmin_bp.route("/hospital-connections")
def hospital_connections():
    hospitals = Hospital.query.all()
    connections = HospitalConnection.query.all()

    return render_template(
        "dashboards/superadmin/hospital_connections.html",
        hospitals=hospitals,
        connections=connections
    )

# -----------------------------
# ADD CONNECTION
# -----------------------------
@superadmin_bp.route("/hospital-connections/add", methods=["POST"])
def add_hospital_connection():
    hospital_from = int(request.form["hospital_from"])
    hospital_to = int(request.form["hospital_to"])
    transfer_cost = float(request.form["transfer_cost"])
    latency = float(request.form["latency_minutes"])
    reliability = float(request.form["reliability"])

    # ❌ Prevent same hospital
    if hospital_from == hospital_to:
        flash("A hospital cannot connect to itself.", "error")
        return redirect(url_for("superadmin.hospital_connections"))

    # ❌ Prevent duplicate A → B
    existing = HospitalConnection.query.filter_by(
        hospital_from=hospital_from,
        hospital_to=hospital_to
    ).first()

    if existing:
        flash("This connection already exists.", "error")
        return redirect(url_for("superadmin.hospital_connections"))

    # ✅ Create A → B
    conn_ab = HospitalConnection(
        hospital_from=hospital_from,
        hospital_to=hospital_to,
        transfer_cost=transfer_cost,
        latency_minutes=latency,
        reliability=reliability
    )

    # ✅ Auto-create B → A if missing
    reverse = HospitalConnection.query.filter_by(
        hospital_from=hospital_to,
        hospital_to=hospital_from
    ).first()

    db.session.add(conn_ab)

    if not reverse:
        conn_ba = HospitalConnection(
            hospital_from=hospital_to,
            hospital_to=hospital_from,
            transfer_cost=transfer_cost,
            latency_minutes=latency,
            reliability=reliability
        )
        db.session.add(conn_ba)

    db.session.commit()
    flash("Hospital connection created successfully.", "success")
    return redirect(url_for("superadmin.hospital_connections"))


# -----------------------------
# DELETE CONNECTION
# -----------------------------
@superadmin_bp.route("/hospital-connections/delete/<int:connection_id>", methods=["POST"])
def delete_hospital_connection(connection_id):
    connection = HospitalConnection.query.get_or_404(connection_id)

    db.session.delete(connection)
    db.session.commit()

    flash("Hospital connection deleted", "success")
    return redirect(url_for("superadmin.hospital_connections"))
