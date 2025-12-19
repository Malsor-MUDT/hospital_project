from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from app.models.admin import Admin

auth_bp = Blueprint("auth", __name__)

# -------------------------------
# Admin / Superadmin Login
# -------------------------------
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

            # Redirect based on role
            if admin.role == 1:
                return redirect(url_for("auth.superadmin_dashboard"))
            else:
                return redirect(url_for("auth.admin_dashboard"))
        else:
            flash("Invalid email or password", "danger")

    return render_template("login.html")

# -------------------------------
# Superadmin Dashboard
# -------------------------------
@auth_bp.route("/superadmin/dashboard")
def superadmin_dashboard():
    if session.get("role") != 1:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))
    return render_template("dashboards/superadmin_dashboard.html")


# -------------------------------
# Admin Dashboard
# -------------------------------
@auth_bp.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))
    return render_template("dashboards/admin_dashboard.html")


# -------------------------------
# Logout Route
# -------------------------------
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("auth.admin_login"))
