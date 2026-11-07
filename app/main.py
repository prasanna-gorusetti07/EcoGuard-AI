import os
import random
import json
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Header, Depends, Body
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import (
    UPLOADS_DIR, REPORTS_DIR, STATIC_DIR, TEMPLATES_DIR, 
    DEFAULT_ACK_SLA_HOURS, DEFAULT_ESCALATION_SLA_HOURS, GEMINI_API_KEY
)
from app.database import (
    init_db, get_connection, log_audit, get_complaint_by_id, 
    get_all_complaints, get_audit_trail, authenticate_user, get_user_by_email
)
from app.ai_service import analyze_waste_image
from app.pdf_generator import generate_complaint_pdf
from app.escalation_service import check_and_process_escalations, simulate_fast_forward_escalation
from app.seed_data import seed_database

# Initialize FastAPI App
app = FastAPI(
    title="ECOGUARD AI",
    description="AI-Powered Illegal Waste Dumping Detection, Monitoring and Complaint Escalation System",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static & file directories
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")

@app.on_event("startup")
def startup_event():
    init_db()
    seed_database()

# ----------------- PAGE ROUTES ----------------- #

@app.get("/", response_class=HTMLResponse)
def index_page():
    index_file = TEMPLATES_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>EcoGuard AI System Initializing...</h1>")
    with open(index_file, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/manifest.json")
def get_manifest():
    manifest_file = STATIC_DIR / "manifest.json"
    if not manifest_file.exists():
        raise HTTPException(status_code=404, detail="Manifest not found")
    return FileResponse(manifest_file, media_type="application/manifest+json")

@app.get("/sw.js")
def get_service_worker():
    sw_file = STATIC_DIR / "sw.js"
    if not sw_file.exists():
        raise HTTPException(status_code=404, detail="Service worker not found")
    return FileResponse(
        sw_file, 
        media_type="application/javascript", 
        headers={"Service-Worker-Allowed": "/"}
    )

# ----------------- REPORTING APIS ----------------- #

# ----------------- AUTHENTICATION APIS ----------------- #

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/auth/login")
def officer_login(credentials: LoginRequest):
    user = authenticate_user(credentials.email, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid officer credentials. Please check email and password.")
    
    # Generate simple session token (base64 encoded JSON with expiration)
    token_payload = {
        "email": user["email"],
        "role": user["role"],
        "full_name": user["full_name"],
        "department": user["department"],
        "exp": (datetime.now() + timedelta(days=1)).isoformat()
    }
    token = base64.b64encode(json.dumps(token_payload).encode()).decode()

    return {
        "success": True,
        "token": token,
        "user": user
    }

@app.get("/api/auth/me")
def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization token missing")
    try:
        token = authorization.split(" ")[1]
        payload = json.loads(base64.b64decode(token.encode()).decode())
        exp = datetime.fromisoformat(payload["exp"])
        if datetime.now() > exp:
            raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
        user = get_user_by_email(payload["email"])
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return {"authenticated": True, "user": user}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or corrupted session token")

@app.get("/api/system/status")
def system_status():
    return {
        "gemini_configured": bool(GEMINI_API_KEY),
        "ai_engine": "Google Gemini 2.5 Flash Vision (Active)" if GEMINI_API_KEY else "EcoGuard Heuristics & Ecological Rule Engine (API key not configured)",
        "database": "SQLite (Online)",
        "gis_service": "Leaflet + OpenStreetMap (Connected)"
    }

# ----------------- CITIZEN TRACKING & PUBLIC METRICS ----------------- #

@app.get("/api/complaints/public/stats")
def public_complaint_stats():
    complaints = get_all_complaints()
    total = len(complaints)
    
    pending_statuses = {"New", "Assigned", "Under Review", "Inspection Pending", "Pending"}
    in_progress_statuses = {"Acknowledged", "Verified", "In Progress", "Action Taken"}
    resolved_statuses = {"Closed", "Resolved"}
    
    pending = sum(1 for c in complaints if c.get("status") in pending_statuses)
    in_progress = sum(1 for c in complaints if c.get("status") in in_progress_statuses)
    resolved = sum(1 for c in complaints if c.get("status") in resolved_statuses)
    
    return {
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "resolved": resolved,
        "escalated": sum(1 for c in complaints if c.get("status") == "Escalated")
    }

@app.get("/api/complaints/track/{complaint_id}")
def track_complaint(complaint_id: str):
    cid = complaint_id.strip()
    complaint = get_complaint_by_id(cid)
    if not complaint:
        raise HTTPException(status_code=404, detail=f"No complaint record found matching ID '{cid}'")
    
    audit = get_audit_trail(cid)
    
    # Calculate tracking step index (0 to 4)
    # Step 0: Lodged, Step 1: AI Verified & Assigned, Step 2: Under Review / Inspection, Step 3: Action Taken, Step 4: Resolved / Closed
    st = complaint.get("status", "New")
    step = 0
    if st in ["Assigned", "Acknowledged"]:
        step = 1
    elif st in ["Inspection Pending", "Under Review", "Verified"]:
        step = 2
    elif st in ["In Progress", "Action Taken"]:
        step = 3
    elif st in ["Closed", "Resolved"]:
        step = 4
    elif st in ["Overdue", "Escalated"]:
        step = 2 # In escalated inspection phase
    
    # Strip sensitive phone numbers from public tracker
    safe_complaint = dict(complaint)
    safe_complaint["reporter_contact"] = "Confidential (Protected)"
    
    return {
        "complaint": safe_complaint,
        "current_step": step,
        "audit_trail": audit
    }

@app.get("/api/complaints/map/pins")
def map_complaint_pins():
    complaints = get_all_complaints()
    pins = []
    for c in complaints:
        pins.append({
            "complaint_id": c["complaint_id"],
            "latitude": c["latitude"],
            "longitude": c["longitude"],
            "primary_category": c.get("primary_category", "Solid Waste"),
            "severity": c.get("severity", "Medium"),
            "status": c.get("status", "New"),
            "location_address": c.get("location_address") or c.get("landmark") or "Pinpointed Location",
            "image_path": c.get("image_path", ""),
            "created_at": c.get("created_at", "")
        })
    return pins

# ----------------- REPORTING APIS ----------------- #

@app.post("/api/ai/preview-image")
async def preview_image(file: UploadFile = File(...)):
    """Instant live AI analysis preview before user submits complaint"""
    allowed_exts = {".jpg", ".jpeg", ".png", ".webp"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_exts:
        raise HTTPException(status_code=400, detail="Invalid file type. Supported formats: JPG, PNG, WEBP")

    temp_path = UPLOADS_DIR / f"temp_{int(datetime.now().timestamp())}_{file.filename}"
    with open(temp_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    try:
        analysis = analyze_waste_image(str(temp_path), file.filename)
        return analysis
    finally:
        if temp_path.exists():
            try:
                os.remove(temp_path)
            except:
                pass

@app.post("/api/complaints/submit")
async def submit_complaint(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    location_address: Optional[str] = Form("Coordinates Pinpointed via GPS"),
    landmark: Optional[str] = Form(""),
    description: Optional[str] = Form(""),
    reporter_type: Optional[str] = Form("Citizen"),
    reporter_name: Optional[str] = Form("Anonymous Citizen"),
    reporter_contact: Optional[str] = Form("")
):
    # Validate image extension
    allowed_exts = {".jpg", ".jpeg", ".png", ".webp"}
    file_ext = Path(image.filename).suffix.lower()
    if file_ext not in allowed_exts:
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload JPG, PNG, or WEBP.")

    # Unique ID generation: EG-2026-XXXX
    random_code = random.randint(1100, 9999)
    complaint_id = f"EG-2026-{random_code}"

    # Save permanent image
    saved_filename = f"{complaint_id}{file_ext}"
    saved_path = UPLOADS_DIR / saved_filename

    image_bytes = await image.read()
    with open(saved_path, "wb") as f:
        f.write(image_bytes)

    # Perform AI Image Analysis
    analysis = analyze_waste_image(str(saved_path), image.filename)

    # Department and Officer Assignment based on waste category
    primary_cat = analysis.get("primary_category", "Mixed Municipal Solid Waste")
    dept = "Municipal Solid Waste Management"
    officer = "Officer S. Sharma (Zone 4)"

    if "Industrial" in primary_cat or "Hazardous" in primary_cat:
        dept = "State Pollution Control Board - Vigilance Cell"
        officer = "Joint Director Dr. V. Murthy"
    elif "Construction" in primary_cat or "C&D" in primary_cat:
        dept = "Town Planning & Enforcement Squad"
        officer = "Inspector S. Mehta"
    elif "Electronic" in primary_cat or "E-Waste" in primary_cat:
        dept = "Zonal Sanitation & Hazardous Materials Wing"
        officer = "Officer R. Kulkarni"

    # Calculate SLA Deadlines
    now = datetime.now()
    ack_deadline = (now + timedelta(hours=DEFAULT_ACK_SLA_HOURS)).strftime("%Y-%m-%d %H:%M:%S")
    esc_deadline = (now + timedelta(hours=DEFAULT_ESCALATION_SLA_HOURS)).strftime("%Y-%m-%d %H:%M:%S")

    # Insert into database
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO complaints (
            complaint_id, reporter_type, reporter_name, reporter_contact,
            image_filename, image_path, latitude, longitude, location_address, landmark,
            description, categories, primary_category, severity, risk_assessment, confidence_score,
            recommended_action, environmental_impact, status, assigned_department,
            assigned_officer, escalation_level, sla_ack_deadline, sla_escalation_deadline
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        complaint_id, reporter_type, reporter_name, reporter_contact,
        saved_filename, f"uploads/{saved_filename}", latitude, longitude, location_address, landmark,
        description, json.dumps(analysis.get("categories", [])), primary_cat, analysis.get("severity", "Medium"),
        analysis.get("risk_assessment", ""), analysis.get("confidence_score", 0.85),
        analysis.get("recommended_action", ""), analysis.get("environmental_impact", ""),
        "New", dept, officer, 0, ack_deadline, esc_deadline
    ))
    conn.commit()
    conn.close()

    # Record initial audit entries
    detail_note = f"Reported at GPS ({latitude:.6f}, {longitude:.6f}). Address: {location_address}"
    if description:
        detail_note += f" | Citizen Note: {description}"

    log_audit(
        complaint_id=complaint_id,
        action="Complaint Lodged",
        performed_by=f"{reporter_type}: {reporter_name}",
        details=detail_note
    )
    log_audit(
        complaint_id=complaint_id,
        action="AI Image Classification Completed",
        performed_by="EcoGuard Gemini Agent",
        details=f"Classified as '{primary_cat}' ({int(analysis.get('confidence_score', 0.85)*100)}% confidence). Severity: {analysis.get('severity')}"
    )
    log_audit(
        complaint_id=complaint_id,
        action="Assigned to Response Unit",
        performed_by="Automated Dispatch Matrix",
        details=f"Routed to {dept} for site inspection by {officer}."
    )

    complaint_data = get_complaint_by_id(complaint_id)
    audit_data = get_audit_trail(complaint_id)

    # Pre-generate PDF in background
    background_tasks.add_task(generate_complaint_pdf, complaint_data, audit_data)

    return {
        "success": True,
        "complaint_id": complaint_id,
        "status": "New",
        "primary_category": primary_cat,
        "categories": analysis.get("categories", []),
        "severity": analysis.get("severity", "Medium"),
        "confidence_score": analysis.get("confidence_score", 0.85),
        "risk_assessment": analysis.get("risk_assessment"),
        "environmental_impact": analysis.get("environmental_impact"),
        "recommended_action": analysis.get("recommended_action"),
        "assigned_department": dept,
        "assigned_officer": officer,
        "created_at": complaint_data.get("created_at")
    }

# ----------------- OFFICER DASHBOARD APIS ----------------- #

@app.get("/api/complaints")
def list_complaints(status: Optional[str] = "All", category: Optional[str] = "All"):
    return get_all_complaints(status=status, category=category)

@app.get("/api/complaints/{complaint_id}")
def complaint_detail(complaint_id: str):
    complaint = get_complaint_by_id(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    audit = get_audit_trail(complaint_id)
    return {
        "complaint": complaint,
        "audit_trail": audit
    }

@app.post("/api/complaints/{complaint_id}/update-status")
def update_complaint_status(
    complaint_id: str,
    status: str = Form(...),
    officer_name: str = Form("Inspecting Officer"),
    inspection_notes: Optional[str] = Form(""),
    action_taken_notes: Optional[str] = Form("")
):
    complaint = get_complaint_by_id(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    conn = get_connection()
    cursor = conn.cursor()

    acknowledged_at = complaint.get("acknowledged_at")
    closed_at = complaint.get("closed_at")

    if status in ["Acknowledged", "Inspection Pending", "Verified", "Under Review", "In Progress"] and not acknowledged_at:
        acknowledged_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if status in ["Closed", "Resolved", "Rejected"]:
        closed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE complaints 
        SET status = ?,
            inspection_notes = COALESCE(NULLIF(?, ''), inspection_notes),
            action_taken_notes = COALESCE(NULLIF(?, ''), action_taken_notes),
            acknowledged_at = COALESCE(?, acknowledged_at),
            closed_at = COALESCE(?, closed_at)
        WHERE complaint_id = ?
    """, (status, inspection_notes, action_taken_notes, acknowledged_at, closed_at, complaint_id))
    conn.commit()
    conn.close()

    # Log audit
    log_detail = f"Status transitioned to '{status}' by {officer_name}."
    if inspection_notes:
        log_detail += f" Inspection Notes: {inspection_notes}."
    if action_taken_notes:
        log_detail += f" Action Taken: {action_taken_notes}."

    log_audit(
        complaint_id=complaint_id,
        action=f"Status Updated: {status}",
        performed_by=officer_name,
        details=log_detail
    )

    return {"success": True, "complaint_id": complaint_id, "new_status": status}

@app.post("/api/complaints/{complaint_id}/reassign")
def reassign_complaint(
    complaint_id: str,
    department: str = Form(...),
    officer_name: str = Form(...)
):
    complaint = get_complaint_by_id(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE complaints 
        SET assigned_department = ?,
            assigned_officer = ?
        WHERE complaint_id = ?
    """, (department, officer_name, complaint_id))
    conn.commit()
    conn.close()

    log_audit(
        complaint_id=complaint_id,
        action="Case Reassigned",
        performed_by="Department Dispatcher",
        details=f"Case reassigned to {department} - Officer: {officer_name}"
    )

    return {"success": True, "complaint_id": complaint_id}

@app.get("/api/complaints/{complaint_id}/generate-pdf")
def get_pdf_report(complaint_id: str):
    complaint = get_complaint_by_id(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    audit = get_audit_trail(complaint_id)
    file_path = generate_complaint_pdf(complaint, audit)

    if file_path.endswith(".pdf"):
        return FileResponse(file_path, media_type="application/pdf", filename=f"EcoGuard_Report_{complaint_id}.pdf")
    else:
        return FileResponse(file_path, media_type="text/html", filename=f"EcoGuard_Report_{complaint_id}.html")

# ----------------- ESCALATION & SLA SIMULATION APIS ----------------- #

@app.post("/api/escalation/process")
def trigger_escalation_checks():
    events = check_and_process_escalations()
    return {"success": True, "processed_count": len(events), "events": events}

@app.post("/api/escalation/simulate/{complaint_id}")
def simulate_escalation_endpoint(complaint_id: str):
    """Judge Demo endpoint: Fast forward SLA delay to showcase automated escalation pipeline"""
    result = simulate_fast_forward_escalation(complaint_id)
    return result

# ----------------- ANALYTICS & HOTSPOTS APIS ----------------- #

@app.get("/api/analytics/kpis")
def get_kpi_metrics():
    complaints = get_all_complaints()
    total = len(complaints)

    status_counts = {
        "New": 0, "Assigned": 0, "Acknowledged": 0, 
        "Inspection Pending": 0, "Verified": 0, "Action Taken": 0, 
        "Closed": 0, "Overdue": 0, "Escalated": 0
    }
    category_counts = {}
    severity_counts = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}

    for c in complaints:
        st = c.get("status", "New")
        status_counts[st] = status_counts.get(st, 0) + 1

        cat = c.get("primary_category", "Mixed Solid Waste")
        category_counts[cat] = category_counts.get(cat, 0) + 1

        sev = c.get("severity", "Medium")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    return {
        "total": total,
        "active_unresolved": total - status_counts.get("Closed", 0),
        "status_breakdown": status_counts,
        "category_breakdown": category_counts,
        "severity_breakdown": severity_counts,
        "escalated_count": status_counts.get("Escalated", 0),
        "overdue_count": status_counts.get("Overdue", 0)
    }

@app.get("/api/analytics/hotspots")
def get_dumping_hotspots():
    """
    Groups reports by spatial proximity (~0.01 deg lat/lng) to identify repeated dumping hotspots.
    """
    complaints = get_all_complaints()
    clusters = []

    # Proximity clustering
    for c in complaints:
        lat = c["latitude"]
        lng = c["longitude"]
        matched = False

        for cluster in clusters:
            if abs(cluster["center_lat"] - lat) < 0.01 and abs(cluster["center_lng"] - lng) < 0.01:
                cluster["count"] += 1
                cluster["complaint_ids"].append(c["complaint_id"])
                cluster["categories"].append(c.get("primary_category", "Mixed Waste"))
                if c.get("severity") in ["High", "Critical"]:
                    cluster["risk_level"] = "Critical"
                matched = True
                break

        if not matched:
            clusters.append({
                "center_lat": lat,
                "center_lng": lng,
                "zone_name": c.get("landmark") or c.get("location_address") or "Identified Hotspot Zone",
                "count": 1,
                "risk_level": "High" if c.get("severity") in ["High", "Critical"] else "Medium",
                "complaint_ids": [c["complaint_id"]],
                "categories": [c.get("primary_category", "Mixed Waste")]
            })

    return clusters

# ----------------- KNOWLEDGE BASE (RAG GUIDANCE) ----------------- #

@app.get("/api/knowledge-base")
def get_environmental_rules():
    """Trusted environmental guidelines for contextual RAG guidance"""
    return [
        {
            "category": "Plastic Waste",
            "statute": "Plastic Waste Management Rules (2016 & Amendments 2021/2022)",
            "key_directives": [
                "Total prohibition on identified single-use plastic commodities under 120 microns.",
                "Mandatory Extended Producer Responsibility (EPR) compliance for commercial packaging entities.",
                "Local municipal bodies authorized to levy spot penalties and confiscate unauthorized commercial stock."
            ],
            "handling_protocol": "Non-destructive mechanical segregation into HDPE, LDPE, PET. Routing to registered Material Recovery Facilities (MRFs) for co-processing in cement kilns or road bitumen mix."
        },
        {
            "category": "Construction & Demolition Debris",
            "statute": "Construction and Demolition Waste Management Rules, 2016",
            "key_directives": [
                "Strict ban on nocturnal roadside dumping and stormwater drain encroachment.",
                "Generators generating over 20 tons/day must submit Waste Management Plan before civil commencement.",
                "Mandatory utilization of recycled aggregates in municipal non-load-bearing civil works."
            ],
            "handling_protocol": "Hydraulic tipper pickup to authorized crushing and recycling plants for production of manufactured sand (M-sand) and paver blocks."
        },
        {
            "category": "Industrial & Hazardous Waste",
            "statute": "Hazardous and Other Wastes (Management & Transboundary Movement) Rules, 2016",
            "key_directives": [
                "Criminal liability under Section 15 of Environment Protection Act for clandestine dumping.",
                "Manifest system (Form 10) mandatory for all transit of contaminated barrels and sludges.",
                "Immediate remediation and financial liability imposed under the Polluter Pays Principle."
            ],
            "handling_protocol": "Deployment of HAZMAT emergency containment team, secondary containment berms, and transportation to TSDF (Treatment, Storage, and Disposal Facility)."
        },
        {
            "category": "Electronic Waste",
            "statute": "E-Waste (Management) Rules, 2022",
            "key_directives": [
                "Complete ban on informal acid-leaching and open burning of printed circuit boards.",
                "Recycling targets legally binding on electronics producers and bulk consumers."
            ],
            "handling_protocol": "Chain-of-custody transfer to authorized dismantlers equipped with mechanized precious metal recovery and HEPA dust filtration."
        }
    ]
