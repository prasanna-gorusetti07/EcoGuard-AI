import json
from datetime import datetime, timedelta
from app.database import get_connection, log_audit, init_db

SAMPLE_COMPLAINTS = [
    {
        "complaint_id": "EG-2026-1001",
        "reporter_type": "Citizen",
        "reporter_name": "Rohan Verma",
        "reporter_contact": "+91 98765 43210",
        "image_filename": "sample_plastic_dump.jpg",
        "image_path": "uploads/sample_plastic_dump.jpg",
        "latitude": 17.4399,
        "longitude": 78.3814,
        "location_address": "Near Hitec City Metro Pillar 114, Madhapur, Hyderabad",
        "landmark": "Adjacent to Stormwater Culvert",
        "categories": ["Single-use Plastics", "Polythene Bags", "Commercial Discards"],
        "primary_category": "Plastic & Packaging Waste",
        "severity": "Medium",
        "risk_assessment": "High risk of stormwater canal blockage prior to monsoon showers; non-biodegradable accumulation.",
        "confidence_score": 0.93,
        "recommended_action": "Deploy segregated plastic waste recovery unit and issue warning to local commercial vendors.",
        "environmental_impact": "Severe macro-plastic degradation polluting local storm drainage.",
        "status": "New",
        "assigned_department": "Municipal Solid Waste Management (West Zone)",
        "assigned_officer": "Officer K. Rao (Ward 104)",
        "escalation_level": 0,
        "escalated_to": None,
        "inspection_notes": None,
        "action_taken_notes": None,
        "created_at": (datetime.now() - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S"),
        "sla_ack_deadline": (datetime.now() + timedelta(hours=18)).strftime("%Y-%m-%d %H:%M:%S"),
        "sla_escalation_deadline": (datetime.now() + timedelta(hours=42)).strftime("%Y-%m-%d %H:%M:%S"),
    },
    {
        "complaint_id": "EG-2026-1002",
        "reporter_type": "Field Officer",
        "reporter_name": "Inspector P. Sundaram",
        "reporter_contact": "+91 91234 56789",
        "image_filename": "sample_construction_debris.jpg",
        "image_path": "uploads/sample_construction_debris.jpg",
        "latitude": 17.4435,
        "longitude": 78.3842,
        "location_address": "Plot 42, Inorbit Mall Bypass Road, Cyberabad",
        "landmark": "Behind Construction Site 3B",
        "categories": ["Concrete Rubble", "Masonry Blocks", "Excavated Earth Debris"],
        "primary_category": "Construction & Demolition (C&D) Waste",
        "severity": "High",
        "risk_assessment": "Illegal nocturnal dumping blocking emergency vehicular lane and creating heavy PM10 particulate dust.",
        "confidence_score": 0.95,
        "recommended_action": "Confiscate unauthorized tipper vehicle; levy statutory penalty under C&D Waste Rules 2016.",
        "environmental_impact": "Soil compaction, dust pollution, traffic hazard.",
        "status": "Inspection Pending",
        "assigned_department": "Town Planning & Enforcement Squad",
        "assigned_officer": "Inspector S. Mehta",
        "escalation_level": 0,
        "escalated_to": None,
        "inspection_notes": "Site visit scheduled for 10:00 AM with municipal tow truck.",
        "action_taken_notes": None,
        "created_at": (datetime.now() - timedelta(hours=18)).strftime("%Y-%m-%d %H:%M:%S"),
        "sla_ack_deadline": (datetime.now() + timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S"),
        "sla_escalation_deadline": (datetime.now() + timedelta(hours=30)).strftime("%Y-%m-%d %H:%M:%S"),
    },
    {
        "complaint_id": "EG-2026-1003",
        "reporter_type": "Citizen",
        "reporter_name": "Ananya Sen",
        "reporter_contact": "+91 94567 89012",
        "image_filename": "sample_chemical_drums.jpg",
        "image_path": "uploads/sample_chemical_drums.jpg",
        "latitude": 17.4410,
        "longitude": 78.3790,
        "location_address": "Kukatpally Lake Perimeter, Near Outer Ring Road Junction",
        "landmark": "Water Body Bank - 50m from shoreline",
        "categories": ["Corrosive Chemical Barrels", "Industrial Effluent Residue", "Heavy Metals"],
        "primary_category": "Industrial & Hazardous Waste",
        "severity": "Critical",
        "risk_assessment": "CRITICAL: Direct leaching of toxic industrial chemicals into municipal water catchment area. Acute toxicity risk.",
        "confidence_score": 0.97,
        "recommended_action": "Emergency HAZMAT deployment, cordoning of lake bank, water sample collection for laboratory spectrometry.",
        "environmental_impact": "Groundwater aquifer toxicity and aquatic ecosystem destruction.",
        "status": "Escalated",
        "assigned_department": "State Pollution Control Board - Vigilance Cell",
        "assigned_officer": "Joint Director Dr. V. Murthy",
        "escalation_level": 2,
        "escalated_to": "Zonal Municipal Commissioner & Pollution Control Magistrate",
        "inspection_notes": "Emergency sample drawn by Vigilance chemist. Barrels sealed.",
        "action_taken_notes": "Criminal case registered under Environment Protection Act Section 15.",
        "created_at": (datetime.now() - timedelta(hours=54)).strftime("%Y-%m-%d %H:%M:%S"),
        "sla_ack_deadline": (datetime.now() - timedelta(hours=30)).strftime("%Y-%m-%d %H:%M:%S"),
        "sla_escalation_deadline": (datetime.now() - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S"),
    },
    {
        "complaint_id": "EG-2026-1004",
        "reporter_type": "Citizen",
        "reporter_name": "Deepak Nair",
        "reporter_contact": "+91 97890 12345",
        "image_filename": "sample_ewaste_dump.jpg",
        "image_path": "uploads/sample_ewaste_dump.jpg",
        "latitude": 17.4470,
        "longitude": 78.3880,
        "location_address": "Industrial Estate Phase 2, Lane 6, Gachibowli",
        "landmark": "Opposite Transformer Yard",
        "categories": ["Cathode Ray Tubes", "Printed Circuit Boards", "Discarded Lithium Batteries"],
        "primary_category": "Electronic Waste (E-Waste)",
        "severity": "High",
        "risk_assessment": "Heavy metal runoff (lead and mercury) into nearby unpaved soil; fire hazard.",
        "confidence_score": 0.91,
        "recommended_action": "Transfer to State Authorized E-Waste Dismantling Facility with chain-of-custody manifest.",
        "environmental_impact": "Bioaccumulative soil toxin contamination.",
        "status": "Overdue",
        "assigned_department": "Zonal Sanitation Wing",
        "assigned_officer": "Officer R. Kulkarni",
        "escalation_level": 1,
        "escalated_to": "Senior Sanitation Superintendent",
        "inspection_notes": None,
        "action_taken_notes": None,
        "created_at": (datetime.now() - timedelta(hours=32)).strftime("%Y-%m-%d %H:%M:%S"),
        "sla_ack_deadline": (datetime.now() - timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S"),
        "sla_escalation_deadline": (datetime.now() + timedelta(hours=16)).strftime("%Y-%m-%d %H:%M:%S"),
    },
    {
        "complaint_id": "EG-2026-1005",
        "reporter_type": "Field Officer",
        "reporter_name": "Sanitary Inspector G. Naidu",
        "reporter_contact": "+91 90123 45678",
        "image_filename": "sample_organic_dump.jpg",
        "image_path": "uploads/sample_organic_dump.jpg",
        "latitude": 17.4380,
        "longitude": 78.3825,
        "location_address": "Rythu Vegetable Wholesale Bazaar Open Yard, Madhapur",
        "landmark": "Market Gate 2",
        "categories": ["Rotting Vegetable Refuse", "Moist Organic Pulp", "Agricultural Waste"],
        "primary_category": "Organic & Biodegradable Waste",
        "severity": "Medium",
        "risk_assessment": "Odor nuisance, fly breeding, potential cholera/gastrointestinal vectors.",
        "confidence_score": 0.89,
        "recommended_action": "Daily wet collection routing directly to decentralized aerobic composting unit.",
        "environmental_impact": "Methane generation and leachate contamination of soil.",
        "status": "Closed",
        "assigned_department": "Municipal Solid Waste Management",
        "assigned_officer": "Officer G. Naidu",
        "escalation_level": 0,
        "escalated_to": None,
        "inspection_notes": "Site inspected. Market association issued directive to maintain segregated bins.",
        "action_taken_notes": "2.5 metric tonnes of organic refuse lifted via compactors to Compost Plant.",
        "created_at": (datetime.now() - timedelta(hours=72)).strftime("%Y-%m-%d %H:%M:%S"),
        "sla_ack_deadline": (datetime.now() - timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S"),
        "sla_escalation_deadline": (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S"),
    }
]

def seed_database():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Check if complaints already exist
    cursor.execute("SELECT COUNT(*) FROM complaints")
    count = cursor.fetchone()[0]
    if count > 0:
        conn.close()
        return

    print("Seeding initial realistic environmental complaints for demonstration...")
    for c in SAMPLE_COMPLAINTS:
        cursor.execute("""
            INSERT INTO complaints (
                complaint_id, reporter_type, reporter_name, reporter_contact,
                image_filename, image_path, latitude, longitude, location_address, landmark,
                categories, primary_category, severity, risk_assessment, confidence_score,
                recommended_action, environmental_impact, status, assigned_department,
                assigned_officer, escalation_level, escalated_to, inspection_notes, action_taken_notes,
                created_at, sla_ack_deadline, sla_escalation_deadline
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            c["complaint_id"], c["reporter_type"], c["reporter_name"], c["reporter_contact"],
            c["image_filename"], c["image_path"], c["latitude"], c["longitude"], c["location_address"], c["landmark"],
            json.dumps(c["categories"]), c["primary_category"], c["severity"], c["risk_assessment"], c["confidence_score"],
            c["recommended_action"], c["environmental_impact"], c["status"], c["assigned_department"],
            c["assigned_officer"], c["escalation_level"], c["escalated_to"], c["inspection_notes"], c["action_taken_notes"],
            c["created_at"], c["sla_ack_deadline"], c["sla_escalation_deadline"]
        ))

        # Seed audit entries for each
        log_audit(
            complaint_id=c["complaint_id"],
            action="Complaint Lodged",
            performed_by=f"{c['reporter_type']}: {c['reporter_name']}",
            details=f"Photograph submitted from coordinates ({c['latitude']}, {c['longitude']}).",
            conn=conn
        )
        log_audit(
            complaint_id=c["complaint_id"],
            action="AI Image Classification Completed",
            performed_by="EcoGuard Gemini Agent",
            details=f"Identified {c['primary_category']} with {int(c['confidence_score']*100)}% confidence rating.",
            conn=conn
        )

        if c["status"] in ["Inspection Pending", "Verified", "Action Taken", "Closed"]:
            log_audit(
                complaint_id=c["complaint_id"],
                action="Officer Acknowledged Case",
                performed_by=c["assigned_officer"],
                details=f"Case assigned to {c['assigned_department']}.",
                conn=conn
            )

        if c["status"] == "Overdue":
            log_audit(
                complaint_id=c["complaint_id"],
                action="SLA Overdue Reminder Issued",
                performed_by="EcoGuard Escalation Engine",
                details="Acknowledgement deadline exceeded. Level 1 reminder dispatched.",
                conn=conn
            )

        if c["status"] == "Escalated":
            log_audit(
                complaint_id=c["complaint_id"],
                action="Level 2 Escalation Triggered",
                performed_by="EcoGuard Escalation Engine",
                details=f"Transferred to {c['escalated_to']} for immediate statutory intervention.",
                conn=conn
            )

        if c["status"] == "Closed":
            log_audit(
                complaint_id=c["complaint_id"],
                action="Remediation Verified & Case Closed",
                performed_by=c["assigned_officer"],
                details="Waste completely removed. Post-clearance photography verified.",
                conn=conn
            )

    conn.commit()
    conn.close()
    print("Seeding complete.")

if __name__ == "__main__":
    seed_database()
