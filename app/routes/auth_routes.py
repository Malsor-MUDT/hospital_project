from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from app.models.admin import Admin
from app.models.doctor import Doctor

auth_bp = Blueprint("auth", __name__)

# -------------------------------
# Admin / Superadmin Login
# -------------------------------
@auth_bp.route("/")
def index():
    return render_template("index.html")

@auth_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        admin = Admin.query.filter_by(email=email).first()

        if admin and check_password_hash(admin.password, password):
            # Save session info
            session["admin_id"] = admin.admin_id
            session["role"] = admin.role
            session["hospital_id"] = admin.hospital_id

            # Redirect based on role
            if admin.role == 1:
                return redirect(url_for("superadmin.dashboard"))
            else:
                return redirect(url_for("admin.dashboard"))
        else:
            flash("Invalid email or password", "danger")

    return render_template("login.html")

# -------------------------------
# Superadmin Dashboard
# -------------------------------
# @auth_bp.route("/superadmin/dashboard")
# def superadmin_dashboard():
#     if session.get("role") != 1:
#         flash("Access denied", "danger")
#         return redirect(url_for("auth.admin_login"))
#     return render_template("dashboards/superadmin_dashboard.html")


# -------------------------------
# Admin Dashboard
# -------------------------------
@auth_bp.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))
    return render_template("dashboards/admin/admin_dashboard.html")

@auth_bp.route("/doctor/login", methods=["GET", "POST"])
def doctor_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        doctor = Doctor.query.filter_by(email=email).first()

        if doctor and check_password_hash(doctor.password, password):
            session["doctor_id"] = doctor.doctor_id
            session["hospital_id"] = doctor.hospital_id
            session["role"] = "doctor"

            return redirect(url_for("doctor.dashboard"))
        else:
            flash("Invalid email or password", "danger")

    return render_template("login_doctor.html")

# -------------------------------
# Logout Route
# -------------------------------
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("auth.admin_login"))
