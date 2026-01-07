# app/routes/superadmin_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from app.models.hospital import Hospital
from app.models.admin import Admin
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
    return render_template("dashboards/superadmin_dashboard.html", hospitals=hospitals, admins=admins)

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
