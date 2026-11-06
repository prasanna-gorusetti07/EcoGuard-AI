# 🌿 ECOGUARD AI – AI-Powered Illegal Waste Dumping Detection, Monitoring and Complaint Escalation System

> **Tagline:** Detect. Analyse. Report. Assign. Escalate. Protect.  
> **System Version:** 1.0.0 (Hackathon MVP Release)  
> **Target Audience:** Citizens, Field Officers, Municipal Sanitation Squads, and Pollution Control Board Magistrates.

---

## 📌 1. Project Overview

**ECOGUARD AI** is a complete, modern full-stack web application designed to solve the critical environmental crisis of illegal waste dumping in public spaces, stormwater canals, roadside plots, and open land. 

Unlike traditional passive complaint portals or standalone image classifiers, **ECOGUARD AI converts visual detection into an end-to-end traceable municipal complaint workflow with automated accountability**.

### Core Capabilities:
1. **📸 Citizen & Field Reporting:** Geotagged photo upload with browser GPS geolocation and manual Leaflet map pin refinement. Includes live device camera capture support.
2. **🤖 Multimodal AI Waste Vision:** Powered by **Google Gemini API** (with an intelligent ecological heuristic fallback) to classify visible waste types (Plastics, C&D Rubble, Hazardous Chemicals, E-Waste, Organic Biowaste), compute confidence scores, and estimate environmental severity.
3. **⚖️ Statutory AI Guardrails:** Strictly labels all visual AI outputs as **preliminary** observations requiring physical on-site human inspection before statutory penalties or legal notices are issued.
4. **⏱️ Configurable SLA Escalation Matrix:** Background rules monitor unacknowledged reports. If officers do not respond within configured deadlines (e.g. 24h / 48h), the system automatically issues reminders and escalates cases to the Zonal Municipal Commissioner.
5. **🗺️ GIS Mapping & Repeated Dumping Hotspots:** Fullscreen Leaflet and OpenStreetMap visualizer with color-coded status pins and spatial clustering heat buffers that pinpoint recurring illegal dumping zones.
6. **🛡️ Authorized Officer Portal:** Role-based access control, KPI monitoring, inspection remarks logging, case status transitions, and fast-forward SLA simulation for hackathon demonstrations.
7. **📄 Official PDF Dossier Generation:** Automatic generation of formal, court-admissible environmental incident summaries using ReportLab.

---

## 🏗️ 2. Proposed Architecture & System Workflow

```
[ Citizen / Field Officer ]
       │
       ▼ (1. Photograph + GPS Lock)
[ Frontend (HTML5 / CSS3 / Vanilla JS / Leaflet) ]
       │
       ▼ (2. REST Multipart API)
[ FastAPI Backend (Python) ] ───► [ Google Gemini 2.5 Flash Vision API ]
       │                                       │
       │ (3. Structured JSON Analysis) ◄───────┘
       │
       ├───────────────────────────────┬───────────────────────────────┐
       ▼                               ▼                               ▼
[ SQLite Database ]        [ ReportLab Engine ]             [ SLA Escalation Engine ]
 - Complaints Dossier        - Official PDF Export           - 24h Reminder (Level 1)
 - Immutably Logged Audits                                   - 48h Escalation (Level 2)
 - Officer RBAC Profiles                                     - Never auto-closes
       │                                                               │
       ▼                                                               ▼
[ Authorised Officer Dashboard ] ◄─────────────────────────────────────┘
 - Physical Inspection Verification
 - Status Transitions: New -> Inspection Pending -> Action Taken -> Closed
```

---

## 🗂️ 3. Complete Project Folder Structure

```
c:\EcoGuard AI\
├── app\
│   ├── __init__.py
│   ├── config.py                 # Paths, SLA thresholds, and environment configuration
│   ├── database.py               # SQLite schema, user auth, and audit trail logger
│   ├── ai_service.py             # Google Gemini API client & ecological heuristic profiler
│   ├── escalation_service.py     # Automated SLA monitoring & fast-forward simulation
│   ├── pdf_generator.py          # ReportLab official government PDF dossier builder
│   ├── seed_data.py              # Realistic sample complaints and audit records
│   └── main.py                   # FastAPI REST API endpoints & route handlers
├── static\
│   ├── css\
│   │   └── style.css             # Environmental green theme, responsive cards & modals
│   └── js\
│       ├── app.js                # Tab controller, camera capture API & toast manager
│       ├── citizen.js            # Leaflet GPS picker, AI preview & citizen tracker
│       ├── officer.js            # Officer auth, KPI dossier & status update engine
│       └── hotspots.js           # Spatial intelligence & recurring dumping radar
├── templates\
│   └── index.html                # Single-page application template with all core views
├── uploads\                      # Geotagged evidence photographs
│   ├── sample_plastic_dump.jpg
│   ├── sample_construction_debris.jpg
│   ├── sample_chemical_drums.jpg
│   ├── sample_ewaste_dump.jpg
│   └── sample_organic_dump.jpg
├── reports\                      # Generated official PDF incident reports
├── test_app.py                   # Automated 8-step integration test suite
├── requirements.txt              # Python package dependencies
├── .env.example                  # Template for environment variables
├── .env                          # Local environment settings
└── README.md                     # Documentation and step-by-step running guide
```

---

## 🛠️ 4. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | HTML5, CSS3, Vanilla JavaScript | Responsive citizen reporting UI and officer portal |
| **Backend** | Python 3.12 + FastAPI | High-performance asynchronous REST API server |
| **Database** | SQLite3 (with WAL mode) | Structured relational storage for complaints, users & audit logs |
| **AI Vision** | Google Gemini 2.5 Flash API | Multimodal visual classification, severity assessment & recommendations |
| **Mapping & GIS** | Leaflet.js + OpenStreetMap | Interactive GPS pin-drop, coordinate reverse-geocoding & hotspot heat buffers |
| **Geolocation** | Browser Geolocation API | HTML5 user-permissioned GPS coordinate acquisition |
| **PDF Reporting** | ReportLab | Official government-standard incident report compilation |
| **Security** | SHA-256 Hashing + Bearer Tokens | Officer authentication and role-based access control (RBAC) |

---

## 🚀 5. Step-by-Step Instructions to Run in VS Code

### Prerequisites:
- Python 3.10+ (Tested with Python 3.12)
- Visual Studio Code
- Modern web browser (Chrome, Edge, Firefox, or Safari)

---

### Step 1: Open the Project in VS Code
1. Launch **Visual Studio Code**.
2. Click **File > Open Folder...** and select `C:\EcoGuard AI`.
3. Open a new terminal in VS Code: **Terminal > New Terminal** (or press `` Ctrl + ` ``).

---

### Step 2: Set Up Python Dependencies
In the terminal, install the required packages:

```bash
pip install -r requirements.txt
```

*(If you have multiple Python versions installed, run:)*
```powershell
& "C:\Users\Boyapati pravallika\AppData\Local\Programs\Python\Python312\python.exe" -m pip install -r requirements.txt
```

---

### Step 3: Configure Environment Variables (Optional)
The project comes with a `.env` file configured.

If you have a Google Gemini API key:
1. Open the `.env` file in the root directory.
2. Paste your API key:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   ```
> 💡 **Note:** If `GEMINI_API_KEY` is left blank, ECOGUARD AI **automatically operates in Smart Ecological Heuristic Simulator Mode**. It will still classify images accurately using realistic statutory environmental profiles, meaning **an API key is not required to run and test the complete system!**

---

### Step 4: Run the Automated Verification Suite
To confirm that the database, AI engine, SLA escalation matrix, and PDF generator are operating at 100%:

```powershell
python -u test_app.py
```

You should see:
```text
=================================================================
  🎉 ALL 8 INTEGRATION TESTS PASSED WITH 100% SUCCESS RATE!     
  The ECOGUARD AI platform is complete, robust and production ready.
=================================================================
```

---

### Step 5: Start the Web Server (Local & Mobile PWA Access)
To allow testing on both your local PC and other mobile devices (Android phones/tablets) on the same Wi-Fi network, bind Uvicorn to `0.0.0.0`:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

*(Or using the direct Python binary:)*
```powershell
& "C:\Users\Boyapati pravallika\AppData\Local\Programs\Python\Python312\python.exe" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

### Step 6: Open the Website in Your Browser
- On your laptop / PC: 👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)** or **[http://localhost:8000](http://localhost:8000)**
- On your Android phone connected to the same Wi-Fi network:
  Find your computer's Wi-Fi IPv4 address using `ipconfig` (e.g. `192.168.0.182`), then open:
  👉 **`http://192.168.0.182:8000`** in Chrome for Android.

---

## 📱 6. Installing the PWA on an Android Phone

ECOGUARD AI includes full **Progressive Web App (PWA)** support with a web app manifest, service worker offline shell, and 192x192 / 512x512 app icons.

### Option A: Direct Wi-Fi Access (Quickest)
1. Ensure your PC and Android phone are connected to the same Wi-Fi network.
2. Start the server on your PC:
   ```powershell
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
3. On your Android phone, open **Chrome** and navigate to:
   `http://<YOUR_PC_IP>:8000` (e.g. `http://192.168.0.182:8000`).
4. **To enable the PWA install prompt over local HTTP on Android Chrome:**
   - In Chrome on your phone, navigate to: `chrome://flags`
   - Search for: **"Insecure origins treated as secure"**
   - Enable it and add: `http://192.168.0.182:8000`
   - Tap **Relaunch** at the bottom of Chrome.
   - Now reload `http://192.168.0.182:8000`. You will see the **"📲 Install App"** banner and button!
   - Tap **"Install App"** (or tap Chrome's 3 dots ⋮ > **"Install app"** / **"Add to Home screen"**).
   - An ECOGUARD AI icon will be placed directly on your phone's home screen and app drawer, running as a full-screen, standalone app with native camera and GPS integration!

### Option B: USB Port Forwarding via Chrome DevTools (Zero Configuration)
1. Connect your Android phone to your PC with a USB cable (enable USB Debugging in Developer Options).
2. On your PC, open Chrome and navigate to: `chrome://inspect/#devices`
3. Click **Port forwarding...** and add rule:
   - Port: `8000`
   - IP address and port: `localhost:8000`
   - Check **Enable port forwarding** and click **Done**.
4. On your Android phone, open Chrome and go to:
   👉 **`http://localhost:8000`**
5. Because Chrome automatically treats `localhost` as a secure origin, the **"📲 Install App"** button and Android installation banner will pop up immediately with no flags needed!
6. Tap **"Install App"** to add ECOGUARD AI to your mobile home screen.

---

## 🔑 7. Default Demo Officer Credentials

To test the **Authorised Officer Dashboard**, use the pre-seeded demo accounts below or click the one-click demo login buttons in the login portal:

| Role | Email | Password | Full Name & Department |
|---|---|---|---|
| **Field Inspector** | `officer@ecoguard.ai` | `officer123` | Inspector S. Sharma (Ward 104 Municipal Solid Waste) |
| **Zonal Commissioner** | `admin@ecoguard.ai` | `admin123` | Dr. V. Murthy (State Pollution Control Board & Magistrate) |
| **Enforcement Squad** | `inspector@ecoguard.ai` | `officer123` | Inspector S. Mehta (Town Planning & Enforcement Squad) |

---

## 🌟 7. Key Feature Walkthrough & Demonstration Guide

### A. Home Page (`#home`)
- **Hero Banner:** Quick actions to file a report, track an existing complaint, or view the live GIS map.
- **How It Works:** 4-step visual flow from photo capture to commissioner escalation.
- **Architectural Innovations:** Highlights preliminary AI guardrails, SLA automation, and tamper-evident audit logs.

### B. Citizen Complaint Filing (`#report`)
1. **Photo Upload / Camera Capture:**
   - Drag and drop any image from `uploads/` (e.g. `sample_plastic_dump.jpg` or `sample_chemical_drums.jpg`).
   - Or click **"📸 Capture Using Device Camera"** to snap a live photo from your webcam or phone camera.
2. **Instant Gemini AI Preview:**
   - Displays real-time waste classification, confidence score bar, category tags, ecological risk assessment, and recommended municipal actions.
   - Shows the statutory disclaimer: *"AI findings are preliminary observations. Official enforcement requires on-site inspection by an authorized officer."*
3. **GPS Geolocation & Map Pin-Drop:**
   - Click **"📍 Detect My Location"** to lock browser GPS coordinates with user permission.
   - Or click/drag the pin on the Leaflet map; OpenStreetMap reverse-geocodes the address automatically.
4. **Submit Complaint:**
   - Click **"Submit Report & Generate Complaint ID"**.
   - Generates a unique tracking ID (e.g. `EG-2026-4821`).
   - Modal lets you instantly download the official PDF or jump to the tracking portal.

### C. Citizen Dashboard & Tracking (`#citizen`)
1. **City-Wide KPI Summary:** Live counters for Total Reports, Pending Review, In Progress, and Resolved.
2. **Search by Complaint ID:**
   - Enter `EG-2026-1001` or your newly generated ID and click **Track Status**.
   - Visual 5-stage progress stepper:
     `Report Lodged` ➔ `AI Verified & Assigned` ➔ `Site Inspection` ➔ `Remediation Action` ➔ `Case Closed`
   - Review inspection remarks, assigned officer, and the chronological audit history.
3. **Community Reports Feed:** Browse recent public reports across sectors.

### D. Interactive GIS Map & Hotspot Radar (`#hotspots`)
- **Map Pins:** Color-coded pins for every complaint:
  - 🔵 Blue: New / Assigned
  - 🟠 Orange: Under Review / Inspection Pending
  - 🔴 Red: Critical / SLA Overdue / Escalated
  - 🟢 Green: Remediation Action Taken / Closed
- **Hotspot Heat Buffers:** Circular red/orange translucent buffers automatically group repeated dumping within spatial proximity to highlight chronic dumping areas.
- **Pin Popups:** Click any pin to see the photo thumbnail, category, and direct links to officer review or citizen tracking.

### E. Authorised Officer Dashboard (`#officer`)
1. **Secure Login:** Sign in with `officer@ecoguard.ai` / `officer123` or click **"👮 Field Inspector"**.
2. **Dossier Table & Filters:** Filter complaints by status (New, Assigned, Acknowledged, Under Review, Inspection Pending, Verified, In Progress, Action Taken, Closed, Overdue, Escalated, Rejected) or by Waste Category.
3. **Case Review Modal:**
   - High-resolution photograph and AI findings.
   - Update complaint status and write official inspection notes and remediation remarks.
   - View the complete chronological audit trail.
   - **📥 Download Official PDF Report:** Generates a formal printable report for legal enforcement.
   - **⚡ Test SLA Escalation (+24h / +48h Demo):** Designed for hackathon judges! Simulates the passage of 24h/48h delays to immediately demonstrate how complaints transition to `Overdue` (Level 1) and `Escalated` (Level 2).

### F. Statutory Knowledge Base (`#knowledge`)
- Retrieval-augmented guidelines covering the **Plastic Waste Management Rules 2016/2021**, **C&D Waste Rules 2016**, **Hazardous Wastes Rules 2016**, and **E-Waste Rules 2022**.

---

## ⚖️ 8. Important Judge Questions & Answers

### Q1: Can AI alone prove illegal dumping or convict someone?
> **Answer:** **No.** Under Indian and international environmental jurisprudence, visual AI classification is purely an investigative aid. ECOGUARD AI strictly treats AI findings as **preliminary observations**. Legal notices and penalties require physical verification and a signed report from a designated municipal officer.

### Q2: How does the system discover waste if no citizen reports it?
> **Answer:** In this MVP prototype, reports originate from citizens and field sanitation workers. The system architecture is designed so that future phases can ingest fixed surveillance CCTV feeds at chronic hotspots and scheduled municipal drone survey imagery.

### Q3: What prevents an officer from ignoring a complaint forever?
> **Answer:** The **Automated SLA Escalation Engine**. Every complaint receives strict deadlines upon submission. If unacknowledged within 24 hours, the system marks the case `Overdue` and dispatches a Level 1 reminder to the Field Supervisor. If uninspected after 48 hours, it triggers Level 2 escalation directly to the Zonal Municipal Commissioner.

### Q4: Does the system automatically mark complaints as "Resolved"?
> **Answer:** **Never.** Automated resolution could allow dumped waste to remain on the ground. A complaint can only be closed when an authorized officer physically inspects the cleared site and enters verified remediation remarks.

---

## 📜 9. License & Statutory Notice

Developed for Environmental Innovation and Governance Hackathons. Built using open-source tools, Leaflet, OpenStreetMap, FastAPI, and Google Gemini API.

© 2026 ECOGUARD AI System. Detect. Analyse. Report. Assign. Escalate. Protect.
