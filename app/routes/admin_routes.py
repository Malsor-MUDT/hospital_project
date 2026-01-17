from flask import Blueprint, render_template,jsonify, request, redirect, url_for, flash, session
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
from app.models.hospital import Hospital
from app.models.hospital_connection import HospitalConnection
from app.models.data_transfer import DataTransfer
from app.models.patient_access import PatientAccess
from app.models.simulations import Simulation
from app.services.simulation_engine import EnhancedSimulation
from app.models.treatment_session import TreatmentSession
from datetime import datetime, timedelta

from app.services.transfer_service import compute_hospital_scores, create_transfer_checksum, build_patient_payload
from app.services.checksum_service import generate_checksum
import uuid
import numpy as np

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/transfers", methods=["GET", "POST"])
def transfer_patient():
    patients = Patient.query.all()
    departments = Department.query.all()
    selected_patient = None
    selected_department = None
    hospitals_options = []

    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        department_id = request.form.get("department_id")
        target_hospital_id = request.form.get("target_hospital_id")

        # Transfer submission
        if patient_id and department_id and target_hospital_id:
            patient = Patient.query.get(patient_id)

            initiated_by = session.get("admin_id")  # <-- Use session instead of flask-login

            transfer = DataTransfer(
                patient_id=patient.patient_id,
                source_hospital=patient.hospital_id,
                target_hospital=int(target_hospital_id),
                department_id=int(department_id),
                initiated_by_staff=initiated_by,
                transfer_status="pending",
                transferred_at=db.func.now()
            )
            db.session.add(transfer)
            db.session.flush()

            create_transfer_checksum(transfer)
            db.session.commit()
            flash(f"Patient {patient.name} transferred successfully!", "success")
            return redirect(url_for("admin.transfer_patient"))

        # Step 1: Patient + Department selected, show hospital options
        elif patient_id and department_id:
            selected_patient = Patient.query.get(patient_id)
            selected_department = Department.query.get(int(department_id))
            hospitals_options = compute_hospital_scores(selected_patient.hospital_id, selected_department.department_id)

    return render_template(
        "dashboards/admin/transfer_patient.html",
        patients=patients,
        departments=departments,
        selected_patient=selected_patient,
        selected_department=selected_department,
        hospitals_options=hospitals_options
    )

@admin_bp.route("/incoming-transfers")
def incoming_transfers():
    hospital_id = session.get("hospital_id")

    transfers = DataTransfer.query.filter_by(
        target_hospital=hospital_id,
        transfer_status="pending"
    ).all()

    return render_template(
        "dashboards/admin/incoming_transfers.html",
        transfers=transfers
    )
@admin_bp.route("/transfer/<int:transfer_id>/accept", methods=["POST"])
def accept_transfer(transfer_id):
    transfer = DataTransfer.query.get_or_404(transfer_id)

    # DEBUG: Print current state
    print(f"DEBUG: Transfer ID: {transfer_id}")
    print(f"DEBUG: Original checksum: {transfer.checksum_original}")
    print(f"DEBUG: Current status: {transfer.transfer_status}")

    # Verify checksum
    from app.services.transfer_service import verify_transfer_checksum
    checksum_matches = verify_transfer_checksum(transfer)
    
    print(f"DEBUG: Checksum matches? {checksum_matches}")
    
    if checksum_matches:
        # Recompute and store verified checksum
        payload = build_patient_payload(transfer.patient_id, transfer.department_id)
        payload["transfer_context"]["timestamp"] = transfer.transferred_at.isoformat() if transfer.transferred_at else None
        verified_checksum = generate_checksum(payload)
        
        print(f"DEBUG: New checksum: {verified_checksum}")
        
        transfer.transfer_status = "verified"
        transfer.checksum_verified = verified_checksum
        
        # Create access record
        access = PatientAccess(
            patient_id=transfer.patient_id,
            hospital_id=transfer.target_hospital,
            access_reason=f"Transfer approved for department {transfer.department_id}",
            transfer_id=transfer.transfer_id,
            access_granted_at=db.func.now(),
            is_active=True
        )
        db.session.add(access)
        
        # COMMIT HERE to ensure changes are saved
        db.session.commit()
        
        flash("Transfer verified successfully! Access granted.", "success")
        print(f"DEBUG: Transfer marked as verified and committed")
    else:
        # Still update the database even if it fails
        transfer.transfer_status = "failed"
        
        # Store what checksum we got (for debugging)
        payload = build_patient_payload(transfer.patient_id, transfer.department_id)
        payload["transfer_context"]["timestamp"] = transfer.transferred_at.isoformat() if transfer.transferred_at else None
        transfer.checksum_verified = generate_checksum(payload)
        
        db.session.commit()
        
        flash("Checksum verification failed. Transfer rejected.", "danger")
        print(f"DEBUG: Transfer marked as failed")

    return redirect(url_for("admin.incoming_transfers"))

@admin_bp.route("/transfer/<int:transfer_id>/reject", methods=["POST"])
def reject_transfer(transfer_id):
    transfer = DataTransfer.query.get_or_404(transfer_id)
    transfer.transfer_status = "rejected"
    db.session.commit()
    flash("Transfer request has been manually rejected.", "warning")
    return redirect(url_for("admin.incoming_transfers"))
@admin_bp.route("/transfers-history")
def transfers_history():
    """
    Shows complete transfer history for the admin's hospital
    - Incoming transfers (to this hospital)
    - Outgoing transfers (from this hospital)
    - Shows department names instead of IDs
    """
    hospital_id = session.get("hospital_id")
    
    # Get incoming transfers (to this hospital)
    incoming_transfers = db.session.query(
        DataTransfer,
        Department.name.label('department_name'),
        Hospital.name.label('source_hospital_name'),
        Patient.name.label('patient_name')
    )\
    .join(Department, DataTransfer.department_id == Department.department_id)\
    .join(Hospital, DataTransfer.source_hospital == Hospital.hospital_id)\
    .join(Patient, DataTransfer.patient_id == Patient.patient_id)\
    .filter(DataTransfer.target_hospital == hospital_id)\
    .order_by(DataTransfer.transferred_at.desc())\
    .all()
    
    # Get outgoing transfers (from this hospital)
    outgoing_transfers = db.session.query(
        DataTransfer,
        Department.name.label('department_name'),
        Hospital.name.label('target_hospital_name'),
        Patient.name.label('patient_name')
    )\
    .join(Department, DataTransfer.department_id == Department.department_id)\
    .join(Hospital, DataTransfer.target_hospital == Hospital.hospital_id)\
    .join(Patient, DataTransfer.patient_id == Patient.patient_id)\
    .filter(DataTransfer.source_hospital == hospital_id)\
    .order_by(DataTransfer.transferred_at.desc())\
    .all()
    
    # Format status for display
    def format_status(status):
        status_map = {
            'pending': ('⏳ Pending', 'bg-yellow-100 text-yellow-800'),
            'verified': ('✅ Verified', 'bg-green-100 text-green-800'),
            'rejected': ('❌ Rejected', 'bg-red-100 text-red-800'),
            'failed': ('⚠️ Failed', 'bg-orange-100 text-orange-800')
        }
        return status_map.get(status, (status, 'bg-gray-100 text-gray-800'))
    
    return render_template(
        "dashboards/admin/transfers_history.html",
        incoming=incoming_transfers,
        outgoing=outgoing_transfers,
        format_status=format_status,
        hospital_id=hospital_id
    )

# AJAX route for patient autocomplete
@admin_bp.route("/autocomplete/patient")
def autocomplete_patient():
    term = request.args.get("q", "")
    patients = Patient.query.filter(Patient.name.ilike(f"%{term}%")).all()
    results = [{"id": p.patient_id, "name": p.name} for p in patients]
    return jsonify(results)

# AJAX route for department autocomplete (excluding current hospital)
@admin_bp.route("/autocomplete/department/<patient_id>")
def autocomplete_department(patient_id):
    term = request.args.get("q", "")
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify([])
    departments = Department.query.filter(
        Department.name.ilike(f"%{term}%"),
        Department.hospital_id != patient.hospital_id
    ).all()
    results = [{"id": d.department_id, "name": d.name, "hospital_id": d.hospital_id} for d in departments]
    return jsonify(results)


@admin_bp.route("/transfer/confirm", methods=["POST"])
def confirm_transfer():
    if session.get("role") != 0:
        flash("Access denied", "danger")
        return redirect(url_for("auth.admin_login"))

    patient_id = request.form.get("patient_id")
    target_hospital_id = request.form.get("target_hospital")
    staff_id = session.get("admin_id")
    patient = Patient.query.get(patient_id)

    transfer = DataTransfer(
        patient_id=patient_id,
        source_hospital=patient.hospital_id,
        target_hospital=target_hospital_id,
        initiated_by_staff=staff_id
    )
    db.session.add(transfer)
    db.session.commit()
    flash(f"Patient {patient.name} transfer initiated.", "success")
    return redirect(url_for("admin.transfer_patient"))
@admin_bp.route("/simulations", methods=["GET", "POST"])
def simulations():
    if "admin_id" not in session:
        flash("Please log in first", "danger")
        return redirect(url_for("auth.admin_login"))

    admin = Admin.query.get(session["admin_id"])
    hospital_id = admin.hospital_id

    devices = Device.query.filter_by(hospital_id=hospital_id).all()
    treatments = Treatment.query.filter_by(hospital_id=hospital_id).all()

    summary = None
    detailed = None
    recommendations = None
    simulation_id = None
    
    # Calculate historical utilization
    historical_utilization = {}
    if devices:
        # Try to get from treatment sessions
        from app.models.treatment_session import TreatmentSession
        from datetime import datetime, timedelta
        
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        total_treatments = TreatmentSession.query.filter_by(
            hospital_id=hospital_id
        ).filter(
            TreatmentSession.created_at >= six_months_ago
        ).count()
        
        if total_treatments > 0:
            for device in devices:
                device_treatments = TreatmentSession.query.filter_by(
                    device_id=device.device_id,
                    hospital_id=hospital_id
                ).filter(
                    TreatmentSession.created_at >= six_months_ago
                ).count()
                historical_utilization[device.device_id] = device_treatments / total_treatments
        else:
            # Default equal distribution
            for device in devices:
                historical_utilization[device.device_id] = 1.0 / len(devices)
    else:
        # No devices
        historical_utilization = {}

    if request.method == "POST":
        try:
            # Get parameters
            base_treatments = float(request.form.get("base_treatments", 120))
            simulation_runs = int(request.form.get("runs", 100))
            seasonality = float(request.form.get("seasonality", 1.0))
            target_margin = float(request.form.get("target_margin", 20)) / 100
            
            # Build device parameters - use historical if not specified
            device_utilization = {}
            price_changes = {}
            maintenance_downtime = {}
            
            for device in devices:
                device_id = device.device_id
                
                # Try to get from form, otherwise use historical
                util_key = f"util_{device_id}"
                if util_key in request.form and request.form[util_key]:
                    device_utilization[device_id] = float(request.form[util_key])
                else:
                    device_utilization[device_id] = historical_utilization.get(device_id, 0.1)
                
                price_changes[device_id] = 1.0  # Default no change
                maintenance_downtime[device_id] = 0.05  # Default 5%
            
            parameters = {
                'base_treatments_per_month': base_treatments,
                'device_utilization_rates': device_utilization,
                'seasonality_factor': seasonality,
                'price_changes': price_changes,
                'maintenance_downtime': maintenance_downtime,
                'simulation_runs': min(simulation_runs, 100)  # Cap at 100
            }
            
            # Run simulation
            simulator = EnhancedSimulation(hospital_id, devices, treatments)
            results = simulator.simulate_month_with_parameters(parameters)
            
            # Generate recommendations
            recommendations = simulator.optimize_prices(results, target_margin)
            
            # Save with the class method - NOW CORRECT
            simulation_id = simulator.save_simulation_simple(parameters, results, recommendations)
            
            if simulation_id:
                flash(f"Simulation completed! ID: {simulation_id}", "success")
            else:
                # Try minimal save as backup
                simulation_id = simulator.save_simulation_minimal(parameters, results)
                if simulation_id:
                    flash("Simulation completed (minimal save)", "info")
                else:
                    flash("Simulation completed but not saved to database", "warning")
            
            summary = results
            detailed = results
            
        except Exception as e:
            db.session.rollback()
            flash(f"Simulation error: {str(e)[:100]}", "danger")
            import traceback
            traceback.print_exc()
    
    return render_template(
        "dashboards/admin/simulations.html",
        devices=devices,
        summary=summary,
        detailed=detailed,
        recommendations=recommendations,
        simulation_id=simulation_id,
        historical_utilization=historical_utilization  
    )
@admin_bp.route("/simulation/<int:simulation_id>")
def view_simulation(simulation_id):
    """View detailed results of a saved simulation"""
    if "admin_id" not in session:
        flash("Please log in first", "danger")
        return redirect(url_for("auth.admin_login"))
    
    admin = Admin.query.get(session["admin_id"])
    simulation = Simulation.query.get_or_404(simulation_id)
    
    # Check if simulation belongs to admin's hospital
    if simulation.hospital_id != admin.hospital_id:
        flash("Access denied", "danger")
        return redirect(url_for("admin.simulations"))
    
    import json
    
    # Parse all data
    parameters = {}
    results = {}
    recommendations = []
    
    # Parse parameters - FIX THIS PART
    try:
        if simulation.parameters:
            parameters = json.loads(simulation.parameters)
            
            # Check for old/new parameter formats and normalize them
            # This handles both old format (base_treatments) and new format (base_treatments_per_month)
            if 'base_treatments_per_month' in parameters:
                parameters['base_treatments'] = parameters['base_treatments_per_month']
            elif 'base_treatments' not in parameters:
                parameters['base_treatments'] = 120.0  # Default
                
            if 'simulation_runs' not in parameters:
                parameters['simulation_runs'] = 100  # Default
                
            if 'simulation_date' not in parameters:
                parameters['simulation_date'] = simulation.simulation_date.strftime('%Y-%m-%d %H:%M')
                
    except Exception as e:
        print(f"Error parsing parameters: {e}")
        # Set default parameters
        parameters = {
            'base_treatments': 120.0,
            'simulation_runs': 100,
            'simulation_date': simulation.simulation_date.strftime('%Y-%m-%d %H:%M')
        }
    
    # Parse results
    try:
        if simulation.results:
            raw_results = json.loads(simulation.results)
            
            if isinstance(raw_results, dict):
                # Check if we have the new format with 'devices' key
                if 'devices' in raw_results:
                    results = raw_results  # Already in correct format
                else:
                    # Old format - transform
                    device_list = []
                    for device in raw_results.get('devices', []):
                        mapped_device = {
                            'device_name': device.get('name', device.get('device_name', 'Unknown Device')),
                            'expected_profit': float(device.get('profit', device.get('expected_profit', 0))),
                            'gross_margin': float(device.get('margin', device.get('gross_margin', 0))),
                            'expected_revenue': float(device.get('revenue', device.get('expected_revenue', 0))),
                            'expected_cost': float(device.get('cost', device.get('expected_cost', 0))),
                            'expected_treatments': float(device.get('treatments', device.get('expected_treatments', 0))),
                            'current_price': float(device.get('current_price', 0)),
                            'variable_cost_per_use': float(device.get('variable_cost_per_use', 0)),
                            'fixed_monthly_cost': float(device.get('fixed_monthly_cost', 0)),
                            'probability_loss': float(device.get('probability_loss', 0)),
                            'risk_level': device.get('risk_level', 'medium'),
                            'breakeven_treatments': float(device.get('breakeven_treatments', 0)) if device.get('breakeven_treatments') else None
                        }
                        device_list.append(mapped_device)
                    
                    results = {
                        'devices': device_list,
                        'device_count': raw_results.get('device_count', len(device_list)),
                        'total_revenue': raw_results.get('total_revenue', sum(d['expected_revenue'] for d in device_list)),
                        'total_profit': raw_results.get('total_profit', sum(d['expected_profit'] for d in device_list))
                    }
            
    except Exception as e:
        print(f"Error parsing results: {e}")
        results = {'devices': [], 'device_count': 0, 'total_revenue': 0, 'total_profit': 0}
    
    # Parse recommendations
    try:
        if simulation.recommendations:
            rec_data = json.loads(simulation.recommendations)
            if isinstance(rec_data, list):
                recommendations = rec_data
    except:
        recommendations = []
    
    return render_template(
        "dashboards/admin/simulation_results.html",
        simulation=simulation,
        parameters=parameters,
        results=results,
        recommendations=recommendations
    )

@admin_bp.route("/simulation-history")
def simulation_history():
    """View all saved simulations"""
    if "admin_id" not in session:
        flash("Please log in first", "danger")
        return redirect(url_for("auth.admin_login"))
    
    admin = Admin.query.get(session["admin_id"])
    simulations = Simulation.query.filter_by(
        hospital_id=admin.hospital_id
    ).order_by(
        Simulation.simulation_date.desc()
    ).all()
    
    return render_template(
        "dashboards/admin/simulation_history.html",
        simulations=simulations
    )

@admin_bp.route("/simulation/<int:simulation_id>/delete", methods=["POST"])
def delete_simulation(simulation_id):
    """Delete a simulation"""
    if "admin_id" not in session:
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    
    admin = Admin.query.get(session["admin_id"])
    simulation = Simulation.query.get_or_404(simulation_id)
    
    if simulation.hospital_id != admin.hospital_id:
        return jsonify({"success": False, "error": "Access denied"}), 403
    
    db.session.delete(simulation)
    db.session.commit()
    
    return jsonify({"success": True})
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
    admin = Admin.query.get(session["admin_id"])

    doctor_minutes = int(request.form.get("doctor_minutes"))
    nurse_minutes = int(request.form.get("nurse_minutes"))

    doctor_wage = float(request.form.get("doctor_hourly_wage"))
    nurse_wage = float(request.form.get("nurse_hourly_wage"))
    base_cost = float(request.form.get("base_machine_cost"))

    cost_per_use = (
        base_cost +
        (doctor_minutes / 60) * doctor_wage +
        (nurse_minutes / 60) * nurse_wage
    )

    new_device = Device(
        hospital_id=admin.hospital_id,
        device_type=request.form.get("device_type"),
        base_machine_cost=base_cost,
        doctor_minutes=doctor_minutes,
        doctor_hourly_wage=doctor_wage,
        nurse_minutes=nurse_minutes,
        nurse_hourly_wage=nurse_wage,
        cost_per_use=round(cost_per_use, 2),
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

    # Fetch form inputs
    base_cost = float(request.form.get("base_machine_cost"))
    doctor_minutes = int(request.form.get("doctor_minutes"))
    doctor_wage = float(request.form.get("doctor_hourly_wage"))
    nurse_minutes = int(request.form.get("nurse_minutes"))
    nurse_wage = float(request.form.get("nurse_hourly_wage"))
    price_per_use = float(request.form.get("price_per_use"))

    # Recalculate cost_per_use
    cost_per_use = base_cost + (doctor_minutes / 60) * doctor_wage + (nurse_minutes / 60) * nurse_wage

    # Update device
    device.device_type = request.form.get("device_type")
    device.base_machine_cost = base_cost
    device.doctor_minutes = doctor_minutes
    device.doctor_hourly_wage = doctor_wage
    device.nurse_minutes = nurse_minutes
    device.nurse_hourly_wage = nurse_wage
    device.cost_per_use = round(cost_per_use, 2)
    device.price_per_use = price_per_use
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

    if Doctor.query.filter_by(email=request.form.get("email")).first():
        flash("Doctor with this email already exists", "danger")
        return redirect(url_for("admin.doctors"))

    doctor = Doctor(
        doctor_id=str(uuid.uuid4()),
        hospital_id=session.get("hospital_id"),
        specialization_id=request.form.get("specialization_id"),
        name=request.form.get("name"),
        email=request.form.get("email"),
        password=generate_password_hash(request.form.get("password")),
        hourly_wage=request.form.get("hourly_wage") or 0,
        hours_per_month=request.form.get("hours_per_month") or 160
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
    doctor.hourly_wage = request.form.get("hourly_wage") or 0
    doctor.hours_per_month = request.form.get("hours_per_month") or 160

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
