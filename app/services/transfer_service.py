# app/services/transfer_service.py
from app.models.hospital_connection import HospitalConnection
from app.models.hospital import Hospital
from app.models.data_transfer import DataTransfer
from app.services.checksum_service import generate_checksum
from app.models.patient import Patient
from app.models.treatment import Treatment
from app.models.treatment_session import TreatmentSession  
from app import db
def build_patient_payload(patient_id, department_id):
    patient = Patient.query.get(patient_id)

    treatment_sessions = TreatmentSession.query.filter_by(
        patient_id=patient_id
    ).order_by(TreatmentSession.created_at).all()

    payload = {
        "patient": {
            "patient_id": patient.patient_id,
            "name": patient.name,
            "email": patient.email,
            "dob": patient.dob.isoformat() if patient.dob else None,
            "current_hospital_id": patient.hospital_id
        },
        "transfer_context": {
            "department_id": department_id,
            "timestamp": None  # Will be filled later
        },
        "treatment_history": [
            {
                "session_id": ts.session_id,
                "treatment_id": ts.treatment_id,
                "hospital_id": ts.hospital_id,
                "device_id": ts.device_id,
                "doctor_id": ts.doctor_id,
                "doctor_minutes": ts.doctor_minutes,
                "nurse_minutes": ts.nurse_minutes,
                "device_cost": ts.device_cost,
                "device_price": ts.device_price,
                "staff_cost": ts.staff_cost,
                "total_price": ts.total_price,
                "profit": ts.profit,
                "notes": ts.notes,
                "created_at": ts.created_at.isoformat() if ts.created_at else None
            }
            for ts in treatment_sessions
        ]
    }
    
    # DEBUG
    import json
    print(f"DEBUG - Payload structure: {json.dumps(payload, indent=2, default=str)}")
    
    return payload


def create_transfer_checksum(transfer: DataTransfer):
    """
    Creates and stores the original checksum for a transfer.
    This is done at the source hospital before sending.
    """
    payload = build_patient_payload(
        transfer.patient_id,
        transfer.department_id
    )
    
    # Remove timestamp from payload for checksum (use transfer timestamp instead)
    # This ensures both sides compute the same checksum
    payload["transfer_context"]["timestamp"] = transfer.transferred_at.isoformat() if transfer.transferred_at else None
    
    checksum = generate_checksum(payload)
    transfer.checksum_original = checksum


def build_graph():
    """Builds hospital connection graph for scoring."""
    connections = HospitalConnection.query.all()
    graph = {}
    for c in connections:
        graph.setdefault(c.hospital_from, []).append({
            "to": c.hospital_to,
            "cost": c.transfer_cost,
            "latency": c.latency_minutes,
            "reliability": c.reliability
        })
    return graph


def score_hospital(graph, source_hospital_id, target_hospital_id):
    """Scores a hospital connection based on reliability, cost, and latency."""
    edges = graph.get(source_hospital_id, [])
    for e in edges:
        if e["to"] == target_hospital_id:
            # Higher score = better (more reliable, cheaper, faster)
            score = e["reliability"] / (1 + e["cost"] + e["latency"])
            return round(score, 4)
    return 0


def get_candidate_hospitals(patient_hospital_id, department_id):
    """Gets hospitals with the requested department (excluding current hospital)."""
    from app.models.hospital import Hospital
    from app.models.department import Department

    hospitals = Hospital.query.join(Department)\
        .filter(Department.department_id == department_id)\
        .filter(Hospital.hospital_id != patient_hospital_id)\
        .all()
    return hospitals


def compute_hospital_scores(patient_hospital_id, department_id):
    """Computes and ranks candidate hospitals for transfer."""
    graph = build_graph()
    hospitals = get_candidate_hospitals(patient_hospital_id, department_id)

    scored = []
    for h in hospitals:
        score = score_hospital(graph, patient_hospital_id, h.hospital_id)
        scored.append({
            "hospital": h,
            "score": score,
            "hospital_id": h.hospital_id,
            "hospital_name": h.name
        })
    
    # Sort by score (descending)
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


# Add this function for verification at target hospital
def verify_transfer_checksum(transfer: DataTransfer):
    """
    Verifies checksum at target hospital.
    Returns True if checksums match, False otherwise.
    """
    payload = build_patient_payload(
        transfer.patient_id,
        transfer.department_id
    )
    
    # Use the original transfer timestamp for consistency
    payload["transfer_context"]["timestamp"] = transfer.transferred_at.isoformat() if transfer.transferred_at else None
    
    new_checksum = generate_checksum(payload)
    original_checksum = transfer.checksum_original
    
    # DEBUG: Print both checksums
    print(f"DEBUG - Original checksum: {original_checksum}")
    print(f"DEBUG - New checksum:      {new_checksum}")
    print(f"DEBUG - Match: {original_checksum == new_checksum}")
    
    return original_checksum == new_checksum