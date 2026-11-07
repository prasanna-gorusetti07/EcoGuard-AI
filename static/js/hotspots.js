// ECOGUARD AI - Live Interactive Map & Repeated Dumping Hotspot GIS Engine

let hotspotMap = null;
let complaintsMarkerGroup = null;
let hotspotBufferGroup = null;

function initHotspotsMap() {
    const mapEl = document.getElementById('leaflet-hotspot-map');
    if (!mapEl || hotspotMap) return;

    hotspotMap = L.map('leaflet-hotspot-map').setView([17.4415, 78.3820], 14);
    window.hotspotMap = hotspotMap;

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors | EcoGuard AI GIS',
        maxZoom: 19
    }).addTo(hotspotMap);

    hotspotBufferGroup = L.layerGroup().addTo(hotspotMap);
    complaintsMarkerGroup = L.layerGroup().addTo(hotspotMap);

    // Auto-invalidate map size on mobile device resize / orientation change
    window.addEventListener('resize', () => {
        if (hotspotMap) hotspotMap.invalidateSize();
    });
    window.addEventListener('orientationchange', () => {
        setTimeout(() => { if (hotspotMap) hotspotMap.invalidateSize(); }, 300);
    });

    loadHotspotsData();
}

async function loadHotspotsData() {
    if (!hotspotMap) return;

    await Promise.all([
        renderComplaintsPins(),
        renderHotspotClusters()
    ]);
}

// 1. Render all complaint markers across the city
async function renderComplaintsPins() {
    if (!complaintsMarkerGroup) return;
    complaintsMarkerGroup.clearLayers();

    try {
        const res = await fetch('/api/complaints/map/pins');
        if (!res.ok) throw new Error('Failed to fetch complaint pins');
        const pins = await res.json();

        pins.forEach(p => {
            // Determine marker color based on status and severity
            let color = '#2563eb'; // Blue default
            if (p.status === 'Closed' || p.status === 'Resolved' || p.status === 'Action Taken') {
                color = '#059669'; // Green
            } else if (p.status === 'Escalated' || p.status === 'Overdue' || p.severity === 'Critical') {
                color = '#dc2626'; // Red
            } else if (p.status === 'Inspection Pending' || p.status === 'Under Review' || p.severity === 'High') {
                color = '#ea580c'; // Orange
            } else if (p.status === 'Acknowledged' || p.status === 'Assigned') {
                color = '#d97706'; // Amber
            }

            const marker = L.circleMarker([p.latitude, p.longitude], {
                radius: 7,
                fillColor: color,
                color: '#ffffff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.95
            }).addTo(complaintsMarkerGroup);

            const popupHtml = `
                <div style="min-width: 220px; font-family: inherit;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <strong style="color: var(--primary-dark); font-size: 13px;">${p.complaint_id}</strong>
                        <span class="badge" style="background:${color}; color:white; font-size:10px;">${p.status}</span>
                    </div>
                    <div style="margin-bottom: 8px;">
                        <img src="/${p.image_path}" style="width: 100%; height: 100px; object-fit: cover; border-radius: 4px;" alt="Waste Photo">
                    </div>
                    <div style="font-size: 12px; font-weight: 700; color: #0f172a; margin-bottom: 2px;">
                        ${p.primary_category}
                    </div>
                    <div style="font-size: 11px; color: #64748b; margin-bottom: 6px;">
                        📍 ${p.location_address}
                    </div>
                    <div style="display: flex; gap: 6px;">
                        <button class="btn btn-secondary btn-sm btn-full" onclick="trackSpecificComplaint('${p.complaint_id}')">
                            Citizen View
                        </button>
                        <button class="btn btn-primary btn-sm btn-full" onclick="inspectLinkedOfficerCase('${p.complaint_id}')">
                            Officer Review
                        </button>
                    </div>
                </div>
            `;

            marker.bindPopup(popupHtml);
        });

    } catch (e) {
        console.error('Error rendering complaint markers', e);
    }
}

// 2. Render recurring dumping hotspot clusters with buffer radii
async function renderHotspotClusters() {
    if (!hotspotBufferGroup) return;
    hotspotBufferGroup.clearLayers();

    try {
        const res = await fetch('/api/analytics/hotspots');
        if (!res.ok) throw new Error('Failed to fetch hotspots');
        const clusters = await res.json();

        let totalHotspots = clusters.length;
        let criticalHotspots = 0;
        let totalDumps = 0;

        clusters.forEach(c => {
            totalDumps += c.count;
            if (c.risk_level === 'Critical' || c.risk_level === 'High') {
                criticalHotspots++;
            }

            const color = c.risk_level === 'Critical' ? '#dc2626' : (c.risk_level === 'High' ? '#ea580c' : '#eab308');
            const radius = Math.min(80 + c.count * 45, 220);

            // Circular Heat Buffer
            const circle = L.circle([c.center_lat, c.center_lng], {
                color: color,
                fillColor: color,
                fillOpacity: 0.28,
                weight: 1.5,
                radius: radius
            }).addTo(hotspotBufferGroup);

            const popupContent = `
                <div style="min-width: 220px; font-family: inherit;">
                    <div style="font-size: 13px; font-weight: bold; color: #0f172a; margin-bottom: 4px;">
                        🔥 Hotspot: ${c.zone_name}
                    </div>
                    <div style="font-size: 11px; margin-bottom: 6px;">
                        <span class="badge ${c.risk_level === 'Critical' ? 'badge-severity-critical' : 'badge-severity-high'}">
                            ${c.risk_level} Risk Recurring Zone
                        </span>
                    </div>
                    <div style="font-size: 12px; color: #334155; margin-bottom: 4px;">
                        <strong>Repeated Violations:</strong> ${c.count} incident(s) detected
                    </div>
                    <div style="font-size: 11px; color: #64748b; margin-bottom: 8px;">
                        <strong>Dominant Types:</strong> ${[...new Set(c.categories)].join(', ')}
                    </div>
                    <button class="btn btn-primary btn-sm btn-full" onclick="inspectLinkedOfficerCase('${c.complaint_ids[0]}')">
                        Inspect Cluster Cases
                    </button>
                </div>
            `;

            circle.bindPopup(popupContent);
        });

        // Update stats banner
        const hCount = document.getElementById('hotspot-count-val');
        const hCrit = document.getElementById('hotspot-critical-val');
        const hInc = document.getElementById('hotspot-incidents-val');

        if (hCount) hCount.innerText = totalHotspots;
        if (hCrit) hCrit.innerText = criticalHotspots;
        if (hInc) hInc.innerText = totalDumps;

    } catch (e) {
        console.error('Error rendering hotspots', e);
    }
}

function inspectLinkedOfficerCase(complaintId) {
    showTab('tab-officer');
    setTimeout(() => {
        if (typeof openComplaintModal === 'function') {
            openComplaintModal(complaintId);
        }
    }, 300);
}

document.addEventListener('DOMContentLoaded', () => {
    initHotspotsMap();
});
