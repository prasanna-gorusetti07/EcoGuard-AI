import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List
from app.database import get_connection, log_audit

def check_and_process_escalations() -> List[Dict[str, Any]]:
    """
    Scans active complaints and applies reminder / escalation rules based on SLA timestamps.
    Returns list of processed events.
    """
    conn = get_connection()
    cursor = conn.cursor()

    now_iso = datetime.now().isoformat()
    processed_events = []

    # 1. Check for Level 0 -> Level 1 (Overdue Acknowledgment Reminder)
    cursor.execute("""
        SELECT * FROM complaints 
        WHERE status IN ('New', 'Assigned') 
          AND escalation_level = 0
          AND sla_ack_deadline IS NOT NULL
          AND sla_ack_deadline <= datetime('now')
    """)
    overdue_ack = [dict(r) for r in cursor.fetchall()]

    for c in overdue_ack:
        cid = c["complaint_id"]
        cursor.execute("""
            UPDATE complaints 
            SET status = 'Overdue',
                escalation_level = 1,
                escalated_to = 'Senior Sanitation Superintendent'
            WHERE complaint_id = ?
        """, (cid,))
        log_audit(
            complaint_id=cid,
            action="SLA Overdue Reminder Issued",
            performed_by="EcoGuard Escalation Engine",
            details="Complaint unacknowledged past SLA deadline. Automated Level 1 reminder dispatched to field supervisor."
        )
        processed_events.append({
            "complaint_id": cid,
            "type": "Reminder",
            "message": f"Reminder issued for {cid} to Senior Sanitation Superintendent"
        })

    # 2. Check for Level 1 -> Level 2 (Severe Escalation to Zonal Commissioner)
    cursor.execute("""
        SELECT * FROM complaints 
        WHERE status IN ('New', 'Assigned', 'Overdue', 'Inspection Pending') 
          AND escalation_level = 1
          AND sla_escalation_deadline IS NOT NULL
          AND sla_escalation_deadline <= datetime('now')
    """)
    overdue_esc = [dict(r) for r in cursor.fetchall()]

    for c in overdue_esc:
        cid = c["complaint_id"]
        cursor.execute("""
            UPDATE complaints 
            SET status = 'Escalated',
                escalation_level = 2,
                escalated_to = 'Zonal Municipal Commissioner & Pollution Control Magistrate'
            WHERE complaint_id = ?
        """, (cid,))
        log_audit(
            complaint_id=cid,
            action="Level 2 Escalation Triggered",
            performed_by="EcoGuard Escalation Engine",
            details="Critical delay: No corrective action recorded within secondary SLA window. Dossier forwarded to Zonal Municipal Commissioner."
        )
        processed_events.append({
            "complaint_id": cid,
            "type": "Escalation",
            "message": f"Escalated {cid} to Zonal Municipal Commissioner"
        })

    conn.commit()
    conn.close()
    return processed_events

def simulate_fast_forward_escalation(complaint_id: str) -> Dict[str, Any]:
    """
    Hackathon Judge Demo Tool:
    Fast-forwards time for a given complaint to demonstrate the automated reminder & escalation workflow immediately.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM complaints WHERE complaint_id = ?", (complaint_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {"success": False, "error": "Complaint not found"}

    c = dict(row)
    current_level = c.get("escalation_level", 0)

    if current_level == 0:
        new_status = "Overdue"
        new_level = 1
        escalated_to = "Senior Sanitation Superintendent"
        action = "SLA Alert & Reminder Dispatched"
        details = "[Judge Simulation: +24h elapsed] Complaint unacknowledged past SLA deadline. Level 1 reminder alert generated."
    elif current_level == 1:
        new_status = "Escalated"
        new_level = 2
        escalated_to = "Zonal Municipal Commissioner & Magistrate"
        action = "Level 2 Executive Escalation"
        details = "[Judge Simulation: +48h elapsed] Site inspection pending without compliance. Case escalated to Zonal Municipal Commissioner for statutory penalty."
    else:
        new_status = "Escalated"
        new_level = 3
        escalated_to = "State Environmental Vigilance Directorate"
        action = "Level 3 Directorate Escalation"
        details = "[Judge Simulation: +72h elapsed] Persistent non-compliance. Transferred to State Environmental Vigilance Directorate."

    cursor.execute("""
        UPDATE complaints 
        SET status = ?,
            escalation_level = ?,
            escalated_to = ?
        WHERE complaint_id = ?
    """, (new_status, new_level, escalated_to, complaint_id))

    conn.commit()
    conn.close()

    log_audit(
        complaint_id=complaint_id,
        action=action,
        performed_by="EcoGuard Escalation Engine (Demo Simulator)",
        details=details
    )

    return {
        "success": True,
        "complaint_id": complaint_id,
        "new_status": new_status,
        "new_level": new_level,
        "escalated_to": escalated_to,
        "message": details
    }
