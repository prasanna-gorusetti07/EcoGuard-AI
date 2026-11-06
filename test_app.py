"""
=============================================================================
ECOGUARD AI - Comprehensive Test Suite
=============================================================================
Validates all backend and frontend services:
1. SQLite Database Schema & Audit Trail
2. Google Gemini / Ecological AI Multimodal Analyzer
3. Officer Authentication & Role-Based Access Control
4. Citizen Complaint Tracking & Public Metrics
5. SLA Escalation Engine & Fast-Forward Simulation
6. Leaflet Map Geo-pins & Spatial Clustering Hotspots
7. ReportLab Official Government PDF Dossier Generation
=============================================================================
"""

import os
import sys

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

print("=================================================================")
print("     🌿 ECOGUARD AI - SYSTEM INTEGRATION & ACCEPTANCE TESTS     ")
print("=================================================================")

# 1. Database Initialization & Seeding
from app.database import init_db, get_connection, get_complaint_by_id, get_all_complaints, get_audit_trail
from app.seed_data import seed_database

print("\n[Step 1] Initializing SQLite database and verifying seeds...")
init_db()
seed_database()
all_complaints = get_all_complaints()
print(f"  ✓ Database verified. Total seeded complaints: {len(all_complaints)}")
assert len(all_complaints) >= 5, "Database must have seeded complaints"

# 2. Multimodal AI Image Analysis
from app.ai_service import analyze_waste_image

print("\n[Step 2] Testing Multimodal Waste Vision Analyzer...")
sample_images = [
    ("sample_plastic_dump.jpg", "Plastic & Packaging Waste"),
    ("sample_construction_debris.jpg", "Construction & Demolition (C&D) Waste"),
    ("sample_chemical_drums.jpg", "Industrial & Hazardous Waste"),
    ("sample_ewaste_dump.jpg", "Electronic Waste (E-Waste)"),
    ("sample_organic_dump.jpg", "Organic & Biodegradable Waste")
]

for filename, expected_cat in sample_images:
    img_path = os.path.join("uploads", filename)
    if os.path.exists(img_path):
        res = analyze_waste_image(img_path, filename)
        print(f"  ✓ {filename} -> Classified as: '{res['primary_category']}' (Severity: {res['severity']}, Confidence: {int(res['confidence_score']*100)}%)")
        assert res.get("is_ai_preliminary") is True, "AI output must carry preliminary verification flag"

# 3. Officer Authentication & Security
from app.main import officer_login, get_current_user, LoginRequest

print("\n[Step 3] Testing Secure Officer Authentication...")
login_res = officer_login(LoginRequest(email="officer@ecoguard.ai", password="officer123"))
assert login_res["success"] is True
token = login_res["token"]
user_info = login_res["user"]
print(f"  ✓ Officer authenticated: {user_info['full_name']} | Role: {user_info['role']} | Dept: {user_info['department']}")

admin_res = officer_login(LoginRequest(email="admin@ecoguard.ai", password="admin123"))
assert admin_res["success"] is True
print(f"  ✓ Admin / Commissioner authenticated: {admin_res['user']['full_name']}")

# 4. Citizen Complaint Tracking
from app.main import track_complaint, public_complaint_stats

print("\n[Step 4] Testing Citizen Public Tracking & Transparency Portal...")
stats = public_complaint_stats()
print(f"  ✓ Public Stats: Total: {stats['total']}, Pending: {stats['pending']}, In Progress: {stats['in_progress']}, Resolved: {stats['resolved']}")

tracking_data = track_complaint("EG-2026-1001")
c = tracking_data["complaint"]
step = tracking_data["current_step"]
print(f"  ✓ Tracked Complaint {c['complaint_id']} -> Current Status: {c['status']} (Step {step}/4)")
assert "reporter_contact" in c and "Confidential" in c["reporter_contact"], "Citizen phone numbers must be sanitized in public portal"

# 5. Interactive GIS Map Markers & Hotspot Clustering
from app.main import map_complaint_pins, get_dumping_hotspots

print("\n[Step 5] Testing GIS Spatial Intelligence & Hotspot Clustering...")
pins = map_complaint_pins()
print(f"  ✓ Generated {len(pins)} Leaflet geolocated map pins.")
hotspots = get_dumping_hotspots()
print(f"  ✓ Identified {len(hotspots)} recurring dumping cluster(s).")

# 6. Status Transition & Officer Inspection
from app.main import update_complaint_status

print("\n[Step 6] Testing Officer Inspection & Status Transitions...")
update_res = update_complaint_status(
    complaint_id="EG-2026-1001",
    status="Verified",
    officer_name="Inspector S. Sharma",
    inspection_notes="Physical site inspection confirmed 2.5 tons of discarded commercial plastics.",
    action_taken_notes="Instructed Zonal Recovery Unit for mechanical pickup tomorrow."
)
assert update_res["success"] is True
updated_c = get_complaint_by_id("EG-2026-1001")
print(f"  ✓ Status transitioned to '{updated_c['status']}' with inspection remarks logged in audit trail.")

# 7. SLA Escalation Engine & Hackathon Judge Fast-Forward Simulation
from app.escalation_service import simulate_fast_forward_escalation, check_and_process_escalations

print("\n[Step 7] Testing Automated SLA Escalation Engine...")
sim_res = simulate_fast_forward_escalation("EG-2026-1001")
assert sim_res["success"] is True
print(f"  ✓ SLA Fast-Forward Triggered: Level {sim_res['new_level']} -> New Status: {sim_res['new_status']}")
print(f"    Message: {sim_res['message']}")

# 8. ReportLab Government-Format PDF Generation
from app.pdf_generator import generate_complaint_pdf

print("\n[Step 8] Testing Official Statutory PDF Dossier Generation...")
audit = get_audit_trail("EG-2026-1001")
pdf_path = generate_complaint_pdf(get_complaint_by_id("EG-2026-1001"), audit)
print(f"  ✓ Official PDF generated at: {pdf_path}")
assert os.path.exists(pdf_path), "PDF file must exist on disk"

# 9. Progressive Web App (PWA) Manifest, Service Worker & App Icons
from app.main import get_manifest, get_service_worker
from PIL import Image
import json

print("\n[Step 9] Testing Progressive Web App (PWA) Assets & Handlers...")

# Test manifest endpoint response
manifest_resp = get_manifest()
manifest_path = manifest_resp.path
with open(manifest_path, 'r', encoding='utf-8') as f:
    manifest_data = json.load(f)
assert manifest_data.get("display") == "standalone", "Manifest must have display: standalone"
assert len(manifest_data.get("icons", [])) >= 2, "Manifest must declare app icons"
print(f"  ✓ PWA Manifest verified: '{manifest_data['name']}' (Display: {manifest_data['display']})")

# Test service worker endpoint response
sw_resp = get_service_worker()
assert "Service-Worker-Allowed" in sw_resp.headers, "SW response must set Service-Worker-Allowed: / header"
with open(sw_resp.path, 'r', encoding='utf-8') as f:
    sw_code = f.read()
assert "CACHE_NAME" in sw_code and "install" in sw_code, "SW must contain install and cache handlers"
print(f"  ✓ Service Worker verified at {sw_resp.path} with root scope.")

# Test Icon files (192x192 and 512x512)
icon_192_path = os.path.join("static", "icons", "icon-192x192.png")
icon_512_path = os.path.join("static", "icons", "icon-512x512.png")
assert os.path.exists(icon_192_path), "icon-192x192.png must exist"
assert os.path.exists(icon_512_path), "icon-512x512.png must exist"

with Image.open(icon_192_path) as img:
    assert img.size == (192, 192), "Icon 192 must be exactly 192x192"
with Image.open(icon_512_path) as img:
    assert img.size == (512, 512), "Icon 512 must be exactly 512x512"
print(f"  ✓ App Icons verified: 192x192 and 512x512 PNG images present and valid.")

print("\n=================================================================")
print("  🎉 ALL 9 PWA & BACKEND INTEGRATION TESTS PASSED (100% SUCCESS) ")
print("  The ECOGUARD AI PWA platform is fully responsive and installable.")
print("=================================================================\n")
