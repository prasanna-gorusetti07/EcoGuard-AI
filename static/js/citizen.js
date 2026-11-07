// ECOGUARD AI - Citizen Reporting, Live AI Vision & Complaint Tracking Engine

let pickerMap = null;
let pickerMarker = null;
let selectedFile = null;

const DEFAULT_LAT = 17.440081;
const DEFAULT_LNG = 78.381442;

// ----------------- MAP & GPS GEOLOCATION ----------------- //

function initPickerMap() {
    const mapElement = document.getElementById('leaflet-picker-map');
    if (!mapElement || pickerMap) return;

    pickerMap = L.map('leaflet-picker-map').setView([DEFAULT_LAT, DEFAULT_LNG], 15);
    window.pickerMap = pickerMap;

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(pickerMap);

    pickerMarker = L.marker([DEFAULT_LAT, DEFAULT_LNG], {
        draggable: true
    }).addTo(pickerMap);

    updateCoordinatesInputs(DEFAULT_LAT, DEFAULT_LNG);

    pickerMarker.on('dragend', function (e) {
        const pos = e.target.getLatLng();
        updateCoordinatesInputs(pos.lat, pos.lng);
        reverseGeocode(pos.lat, pos.lng);
    });

    pickerMap.on('click', function (e) {
        pickerMarker.setLatLng(e.latlng);
        updateCoordinatesInputs(e.latlng.lat, e.latlng.lng);
        reverseGeocode(e.latlng.lat, e.latlng.lng);
    });

    // Invalidate map dimensions on window resize and mobile device orientation change
    window.addEventListener('resize', () => {
        if (pickerMap) pickerMap.invalidateSize();
    });
    window.addEventListener('orientationchange', () => {
        setTimeout(() => { if (pickerMap) pickerMap.invalidateSize(); }, 300);
    });
}

function updateCoordinatesInputs(lat, lng) {
    const latInput = document.getElementById('form-lat');
    const lngInput = document.getElementById('form-lng');
    if (latInput) latInput.value = lat.toFixed(6);
    if (lngInput) lngInput.value = lng.toFixed(6);
}

function detectLocation() {
    const btn = document.getElementById('btn-detect-gps');
    if (!navigator.geolocation) {
        showToast('Geolocation is not supported by your browser.', 'danger');
        return;
    }

    btn.innerHTML = '⏳ Locking GPS Satellite Signal...';
    btn.disabled = true;

    navigator.geolocation.getCurrentPosition(
        (pos) => {
            const lat = pos.coords.latitude;
            const lng = pos.coords.longitude;
            if (pickerMap && pickerMarker) {
                pickerMap.setView([lat, lng], 17);
                pickerMarker.setLatLng([lat, lng]);
            }
            updateCoordinatesInputs(lat, lng);
            reverseGeocode(lat, lng);
            btn.innerHTML = '📍 Detect My Location';
            btn.disabled = false;
            showToast('GPS coordinates accurately locked with user permission!', 'success');
        },
        (err) => {
            btn.innerHTML = '📍 Detect My Location';
            btn.disabled = false;
            showToast('Could not acquire GPS: ' + err.message + '. Please drag pin on the map.', 'warning');
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
}

async function reverseGeocode(lat, lng) {
    try {
        const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`);
        if (res.ok) {
            const data = await res.json();
            if (data.display_name) {
                const addrInput = document.getElementById('form-address');
                if (addrInput) addrInput.value = data.display_name;
            }
        }
    } catch (e) {
        // Silent fallback
    }
}

// ----------------- IMAGE UPLOAD & PREVIEW ----------------- //

function setupDropzone() {
    const dropzone = document.getElementById('image-dropzone');
    const fileInput = document.getElementById('waste-file-input');
    const previewContainer = document.getElementById('preview-container');
    const previewImg = document.getElementById('preview-img');
    const removeBtn = document.getElementById('remove-img-btn');

    if (!dropzone || !fileInput) return;

    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleImageSelected(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            handleImageSelected(e.target.files[0]);
        }
    });

    // Native mobile camera input listener
    const cameraInput = document.getElementById('camera-file-input');
    if (cameraInput) {
        cameraInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files[0]) {
                handleImageSelected(e.target.files[0]);
            }
        });
    }

    if (removeBtn) {
        removeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            selectedFile = null;
            fileInput.value = '';
            if (previewContainer) previewContainer.style.display = 'none';
            dropzone.style.display = 'block';
            const aiBox = document.getElementById('ai-preview-box');
            if (aiBox) aiBox.style.display = 'none';
        });
    }
}

function handleImageSelected(file) {
    selectedFile = file;
    const dropzone = document.getElementById('image-dropzone');
    const previewContainer = document.getElementById('preview-container');
    const previewImg = document.getElementById('preview-img');

    const reader = new FileReader();
    reader.onload = (e) => {
        if (previewImg) previewImg.src = e.target.result;
        if (dropzone) dropzone.style.display = 'none';
        if (previewContainer) previewContainer.style.display = 'block';
    };
    reader.readAsDataURL(file);

    // Instant live AI classification preview
    runAiPreview(file);
}

async function runAiPreview(file) {
    const aiBox = document.getElementById('ai-preview-box');
    const aiLoading = document.getElementById('ai-preview-loading');
    const aiResult = document.getElementById('ai-preview-result');

    if (!aiBox) return;

    aiBox.style.display = 'block';
    if (aiLoading) aiLoading.style.display = 'block';
    if (aiResult) aiResult.style.display = 'none';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/api/ai/preview-image', {
            method: 'POST',
            body: formData
        });

        if (!res.ok) throw new Error('AI analysis preview failed');
        const data = await res.json();

        // Populate AI Box
        document.getElementById('ai-primary-cat').innerText = data.primary_category;
        
        const sevBadge = document.getElementById('ai-severity-badge');
        if (sevBadge) {
            sevBadge.className = `badge badge-severity-${(data.severity || 'medium').toLowerCase()}`;
            sevBadge.innerText = data.severity + ' Severity';
        }
        
        const confPct = Math.round((data.confidence_score || 0.85) * 100);
        const confText = document.getElementById('ai-conf-text');
        const confFill = document.getElementById('ai-conf-fill');
        if (confText) confText.innerText = `${confPct}% Confidence`;
        if (confFill) confFill.style.width = `${confPct}%`;

        // Category Tags
        const tagsContainer = document.getElementById('ai-category-tags');
        if (tagsContainer) {
            tagsContainer.innerHTML = '';
            (data.categories || []).forEach(cat => {
                const tag = document.createElement('span');
                tag.className = 'badge badge-assigned';
                tag.style.marginRight = '4px';
                tag.style.marginBottom = '4px';
                tag.innerText = cat;
                tagsContainer.appendChild(tag);
            });
        }

        const riskDesc = document.getElementById('ai-risk-desc');
        const actionDesc = document.getElementById('ai-action-desc');
        if (riskDesc) riskDesc.innerText = data.risk_assessment || 'Standard observation.';
        if (actionDesc) actionDesc.innerText = data.recommended_action || 'Inspection recommended.';

        if (aiLoading) aiLoading.style.display = 'none';
        if (aiResult) aiResult.style.display = 'block';

    } catch (err) {
        if (aiLoading) aiLoading.style.display = 'none';
        if (aiBox) aiBox.style.display = 'none';
        showToast('AI preview: Full analysis will execute upon formal submission.', 'info');
    }
}

// ----------------- SUBMIT COMPLAINT FORM ----------------- //

async function submitComplaintForm(e) {
    e.preventDefault();

    if (!selectedFile) {
        showToast('Please upload or snap a waste photograph first.', 'danger');
        return;
    }

    const submitBtn = document.getElementById('btn-submit-complaint');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '⏳ Processing with Gemini AI & Generating Unique Complaint ID...';

    const formData = new FormData();
    formData.append('image', selectedFile);
    formData.append('latitude', document.getElementById('form-lat').value || DEFAULT_LAT);
    formData.append('longitude', document.getElementById('form-lng').value || DEFAULT_LNG);
    formData.append('location_address', document.getElementById('form-address').value || 'Coordinates Pinpointed via GPS');
    formData.append('landmark', document.getElementById('form-landmark').value || '');
    formData.append('description', document.getElementById('form-description').value || '');
    formData.append('reporter_type', document.getElementById('form-reporter-type').value || 'Citizen');
    formData.append('reporter_name', document.getElementById('form-reporter-name').value || 'Anonymous Citizen');
    formData.append('reporter_contact', document.getElementById('form-reporter-contact').value || '');

    try {
        const res = await fetch('/api/complaints/submit', {
            method: 'POST',
            body: formData
        });

        if (!res.ok) throw new Error('Submission failed');
        const data = await res.json();

        // Show Success Modal
        showSubmissionSuccess(data);
        resetReportForm();
        showToast(`Complaint registered successfully! ID: ${data.complaint_id}`, 'success');

    } catch (err) {
        showToast('Error registering complaint: ' + err.message, 'danger');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '🚀 Submit Report & Generate Complaint ID';
    }
}

function showSubmissionSuccess(data) {
    const modal = document.getElementById('success-modal');
    document.getElementById('success-cid').innerText = data.complaint_id;
    document.getElementById('success-category').innerText = data.primary_category;
    document.getElementById('success-severity').innerText = data.severity;
    document.getElementById('success-dept').innerText = data.assigned_department;
    document.getElementById('success-officer').innerText = data.assigned_officer;

    const pdfBtn = document.getElementById('success-pdf-btn');
    if (pdfBtn) {
        pdfBtn.onclick = () => {
            window.open(`/api/complaints/${data.complaint_id}/generate-pdf`, '_blank');
        };
    }

    const trackBtn = document.getElementById('success-track-btn');
    if (trackBtn) {
        trackBtn.onclick = () => {
            modal.classList.remove('active');
            showTab('tab-citizen');
            document.getElementById('track-complaint-id').value = data.complaint_id;
            searchComplaintTracking();
        };
    }

    modal.classList.add('active');
}

function resetReportForm() {
    selectedFile = null;
    const fileInput = document.getElementById('waste-file-input');
    if (fileInput) fileInput.value = '';
    const cameraInput = document.getElementById('camera-file-input');
    if (cameraInput) cameraInput.value = '';
    const prev = document.getElementById('preview-container');
    if (prev) prev.style.display = 'none';
    const dropzone = document.getElementById('image-dropzone');
    if (dropzone) dropzone.style.display = 'block';
    const aiBox = document.getElementById('ai-preview-box');
    if (aiBox) aiBox.style.display = 'none';
    const landmark = document.getElementById('form-landmark');
    if (landmark) landmark.value = '';
    const desc = document.getElementById('form-description');
    if (desc) desc.value = '';
}

// ----------------- CITIZEN DASHBOARD & TRACKING ----------------- //

async function loadCitizenDashboard() {
    await Promise.all([
        loadPublicStats(),
        loadRecentPublicComplaints()
    ]);
}

async function loadPublicStats() {
    try {
        const res = await fetch('/api/complaints/public/stats');
        if (!res.ok) return;
        const data = await res.json();

        const totalEl = document.getElementById('public-stat-total');
        const pendingEl = document.getElementById('public-stat-pending');
        const inProgEl = document.getElementById('public-stat-inprogress');
        const resolvedEl = document.getElementById('public-stat-resolved');

        if (totalEl) totalEl.innerText = data.total;
        if (pendingEl) pendingEl.innerText = data.pending;
        if (inProgEl) inProgEl.innerText = data.in_progress;
        if (resolvedEl) resolvedEl.innerText = data.resolved;
    } catch (e) {
        console.error('Error loading public stats', e);
    }
}

async function loadRecentPublicComplaints() {
    const container = document.getElementById('public-complaints-feed');
    if (!container) return;

    container.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 30px; color: #64748b;">⏳ Loading community environmental reports...</div>';

    try {
        const res = await fetch('/api/complaints');
        if (!res.ok) throw new Error('Could not fetch complaints');
        const list = await res.json();

        if (list.length === 0) {
            container.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 30px; color: #64748b;">No complaints submitted yet. Be the first to report!</div>';
            return;
        }

        container.innerHTML = '';
        list.slice(0, 12).forEach(c => {
            const card = document.createElement('div');
            card.className = 'feed-card';

            let statusClass = 'badge-new';
            if (c.status === 'Inspection Pending' || c.status === 'Under Review') statusClass = 'badge-pending';
            else if (c.status === 'Acknowledged' || c.status === 'Verified') statusClass = 'badge-acknowledged';
            else if (c.status === 'Action Taken' || c.status === 'In Progress') statusClass = 'badge-action';
            else if (c.status === 'Closed' || c.status === 'Resolved') statusClass = 'badge-closed';
            else if (c.status === 'Overdue') statusClass = 'badge-overdue';
            else if (c.status === 'Escalated') statusClass = 'badge-escalated';

            card.innerHTML = `
                <img src="/${c.image_path}" class="feed-card-img" alt="Waste photograph">
                <div class="feed-card-body">
                    <div class="feed-card-header">
                        <span style="font-weight: 800; font-size: 13px; color: var(--primary-dark);">${c.complaint_id}</span>
                        <span class="badge ${statusClass}">${c.status}</span>
                    </div>
                    <div class="feed-card-title">${c.primary_category}</div>
                    <div class="feed-card-location">📍 ${c.location_address || c.landmark || 'GPS Pinpointed'}</div>
                    <div style="margin-top: auto; display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 11px; color: #64748b;">${c.created_at ? c.created_at.slice(0, 10) : ''}</span>
                        <button class="btn btn-secondary btn-sm" onclick="trackSpecificComplaint('${c.complaint_id}')">
                            Track Status
                        </button>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });

    } catch (e) {
        container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: red;">Error: ${e.message}</div>`;
    }
}

function trackSpecificComplaint(complaintId) {
    const input = document.getElementById('track-complaint-id');
    if (input) input.value = complaintId;
    searchComplaintTracking();
    window.scrollTo({ top: document.getElementById('tracking-card-container').offsetTop - 80, behavior: 'smooth' });
}

async function searchComplaintTracking() {
    const input = document.getElementById('track-complaint-id');
    const resultBox = document.getElementById('tracking-result-box');
    const loadingBox = document.getElementById('tracking-loading');

    if (!input || !input.value.trim()) {
        showToast('Please enter a Complaint ID (e.g. EG-2026-1001)', 'warning');
        return;
    }

    const cid = input.value.trim();
    if (loadingBox) loadingBox.style.display = 'block';
    if (resultBox) resultBox.style.display = 'none';

    try {
        const res = await fetch(`/api/complaints/track/${encodeURIComponent(cid)}`);
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Complaint not found');
        }
        const data = await res.json();
        const c = data.complaint;
        const currentStep = data.current_step; // 0 to 4
        const audit = data.audit_trail;

        // Render Stepper
        const steps = document.querySelectorAll('.tracking-step');
        steps.forEach((stepEl, idx) => {
            stepEl.classList.remove('active', 'completed');
            if (idx < currentStep) {
                stepEl.classList.add('completed');
            } else if (idx === currentStep) {
                stepEl.classList.add('active');
            }
        });

        // Populate Complaint Details
        document.getElementById('track-res-id').innerText = c.complaint_id;
        document.getElementById('track-res-status').innerText = c.status;
        document.getElementById('track-res-status').className = `badge badge-${c.status.toLowerCase().replace(' ', '-')}`;
        
        document.getElementById('track-res-img').src = `/${c.image_path}`;
        document.getElementById('track-res-cat').innerText = c.primary_category;
        document.getElementById('track-res-severity').innerText = `${c.severity} Severity`;
        document.getElementById('track-res-loc').innerText = c.location_address || c.landmark || 'GPS Pinpointed';
        document.getElementById('track-res-dept').innerText = c.assigned_department;
        document.getElementById('track-res-officer').innerText = c.assigned_officer;
        document.getElementById('track-res-date').innerText = c.created_at;

        // Inspection & Action Remarks
        const inspectNotes = c.inspection_notes || 'Pending initial field verification by assigned officer.';
        document.getElementById('track-res-inspect').innerText = inspectNotes;

        const actionNotes = c.action_taken_notes || (c.status === 'Closed' ? 'Waste cleared and site restored.' : 'Remediation scheduled.');
        document.getElementById('track-res-action').innerText = actionNotes;

        // PDF Button
        const pdfBtn = document.getElementById('track-res-pdf-btn');
        if (pdfBtn) {
            pdfBtn.onclick = () => window.open(`/api/complaints/${c.complaint_id}/generate-pdf`, '_blank');
        }

        // Render Public Timeline
        const timelineBox = document.getElementById('track-res-timeline');
        if (timelineBox) {
            timelineBox.innerHTML = '';
            (audit || []).forEach(item => {
                const div = document.createElement('div');
                div.className = 'timeline-item';
                div.innerHTML = `
                    <div class="timeline-dot"></div>
                    <div class="timeline-content">
                        <div class="timeline-time">${item.timestamp}</div>
                        <div class="timeline-title">${item.action}</div>
                        <div class="timeline-desc">${item.details || ''}</div>
                    </div>
                `;
                timelineBox.appendChild(div);
            });
        }

        if (loadingBox) loadingBox.style.display = 'none';
        if (resultBox) resultBox.style.display = 'block';

    } catch (e) {
        if (loadingBox) loadingBox.style.display = 'none';
        showToast(e.message, 'danger');
    }
}

// ----------------- KNOWLEDGE BASE LOADER ----------------- //

async function loadKnowledgeBase() {
    const container = document.getElementById('kb-rules-container');
    if (!container) return;

    try {
        const res = await fetch('/api/knowledge-base');
        if (!res.ok) return;
        const list = await res.json();

        container.innerHTML = '';
        list.forEach(item => {
            const card = document.createElement('div');
            card.className = 'kb-card';
            
            let directivesHtml = '';
            item.key_directives.forEach(d => {
                directivesHtml += `<li>${d}</li>`;
            });

            card.innerHTML = `
                <h3>${item.category}</h3>
                <div class="kb-statute">${item.statute}</div>
                <ul class="kb-directives">${directivesHtml}</ul>
                <div class="kb-protocol">
                    <strong>Handling & Recovery Protocol:</strong><br>${item.handling_protocol}
                </div>
            `;
            container.appendChild(card);
        });
    } catch (e) {
        console.error('Error loading knowledge base', e);
    }
}

// ----------------- DOM READY INITIALIZER ----------------- //

document.addEventListener('DOMContentLoaded', () => {
    initPickerMap();
    setupDropzone();

    const gpsBtn = document.getElementById('btn-detect-gps');
    if (gpsBtn) gpsBtn.addEventListener('click', detectLocation);

    const form = document.getElementById('report-complaint-form');
    if (form) form.addEventListener('submit', submitComplaintForm);

    const trackBtn = document.getElementById('btn-search-tracking');
    if (trackBtn) trackBtn.addEventListener('click', searchComplaintTracking);

    const trackInput = document.getElementById('track-complaint-id');
    if (trackInput) {
        trackInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                searchComplaintTracking();
            }
        });
    }

    const closeSuccessBtn = document.getElementById('close-success-modal');
    if (closeSuccessBtn) {
        closeSuccessBtn.addEventListener('click', () => {
            document.getElementById('success-modal').classList.remove('active');
        });
    }
});
