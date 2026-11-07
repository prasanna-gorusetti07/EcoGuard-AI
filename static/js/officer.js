// ECOGUARD AI - Officer Portal, Authentication & Case Review Engine

let activeComplaintId = null;

// ----------------- AUTHENTICATION VIEW HANDLER ----------------- //

function checkOfficerAuthAndRender() {
    const token = getOfficerToken();
    const user = getOfficerUser();

    const loginView = document.getElementById('officer-login-view');
    const dashboardView = document.getElementById('officer-dashboard-view');

    if (!loginView || !dashboardView) return;

    if (!token || !user) {
        loginView.style.display = 'block';
        dashboardView.style.display = 'none';
    } else {
        loginView.style.display = 'none';
        dashboardView.style.display = 'block';

        // Update Officer Strip
        const nameEl = document.getElementById('officer-profile-name');
        const deptEl = document.getElementById('officer-profile-dept');
        const roleEl = document.getElementById('officer-profile-role');

        if (nameEl) nameEl.innerText = user.full_name;
        if (deptEl) deptEl.innerText = user.department;
        if (roleEl) roleEl.innerText = user.role.toUpperCase();

        loadOfficerDashboard();
    }
}

async function handleOfficerLogin(e) {
    if (e) e.preventDefault();

    const email = document.getElementById('officer-email-input').value.trim();
    const password = document.getElementById('officer-password-input').value.trim();
    const btn = document.getElementById('btn-officer-login');

    if (!email || !password) {
        showToast('Please enter officer email and password.', 'warning');
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '⏳ Authenticating Official Credentials...';

    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Authentication failed');
        }

        const data = await res.json();
        setOfficerAuth(data.token, data.user);
        showToast(`Welcome back, ${data.user.full_name}!`, 'success');
        checkOfficerAuthAndRender();

    } catch (err) {
        showToast(err.message, 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '🔐 Secure Officer Sign-In';
    }
}

function quickDemoLogin(email, password) {
    document.getElementById('officer-email-input').value = email;
    document.getElementById('officer-password-input').value = password;
    handleOfficerLogin(null);
}

// ----------------- DASHBOARD DATA LOADING ----------------- //

async function loadOfficerDashboard() {
    await Promise.all([
        loadKpis(),
        loadComplaintsTable()
    ]);
}

async function loadKpis() {
    try {
        const res = await fetch('/api/analytics/kpis');
        if (!res.ok) return;
        const data = await res.json();

        const totalEl = document.getElementById('kpi-total-val');
        const activeEl = document.getElementById('kpi-active-val');
        const overdueEl = document.getElementById('kpi-overdue-val');
        const escEl = document.getElementById('kpi-escalated-val');
        const closedEl = document.getElementById('kpi-closed-val');

        if (totalEl) totalEl.innerText = data.total;
        if (activeEl) activeEl.innerText = data.active_unresolved;
        if (overdueEl) overdueEl.innerText = data.overdue_count;
        if (escEl) escEl.innerText = data.escalated_count;
        if (closedEl) closedEl.innerText = (data.status_breakdown.Closed || 0) + (data.status_breakdown.Resolved || 0);

    } catch (e) {
        console.error("Error loading KPIs", e);
    }
}

async function loadComplaintsTable() {
    const statusFilter = document.getElementById('filter-status') ? document.getElementById('filter-status').value : 'All';
    const categoryFilter = document.getElementById('filter-category') ? document.getElementById('filter-category').value : 'All';
    const tableBody = document.getElementById('complaints-table-body');

    if (!tableBody) return;

    tableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 24px; color: #64748b;">⏳ Loading verified complaints dossier...</td></tr>`;

    try {
        const res = await fetch(`/api/complaints?status=${encodeURIComponent(statusFilter)}&category=${encodeURIComponent(categoryFilter)}`);
        if (!res.ok) throw new Error('Failed to fetch complaints');
        const list = await res.json();

        if (list.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 28px; color: #64748b;">No complaints found matching current filter.</td></tr>`;
            return;
        }

        tableBody.innerHTML = '';
        list.forEach(c => {
            const tr = document.createElement('tr');

            let statusClass = 'badge-new';
            if (c.status === 'Inspection Pending' || c.status === 'Under Review') statusClass = 'badge-pending';
            else if (c.status === 'Acknowledged' || c.status === 'Verified') statusClass = 'badge-acknowledged';
            else if (c.status === 'Action Taken' || c.status === 'In Progress') statusClass = 'badge-action';
            else if (c.status === 'Closed' || c.status === 'Resolved') statusClass = 'badge-closed';
            else if (c.status === 'Overdue') statusClass = 'badge-overdue';
            else if (c.status === 'Escalated') statusClass = 'badge-escalated';
            else if (c.status === 'Rejected') statusClass = 'badge-overdue';

            const sevClass = `badge-severity-${(c.severity || 'medium').toLowerCase()}`;

            let escBadge = '';
            if (c.escalation_level > 0 || c.status === 'Escalated' || c.status === 'Overdue') {
                escBadge = `<span class="badge badge-overdue" style="margin-left:4px;">L${c.escalation_level || 1} SLA Alert</span>`;
            }

            tr.innerHTML = `
                <td><strong>${c.complaint_id}</strong></td>
                <td>
                    <img src="/${c.image_path}" style="width: 52px; height: 38px; object-fit: cover; border-radius: 4px; border: 1px solid #e2e8f0;" alt="Waste">
                </td>
                <td>
                    <strong>${c.primary_category}</strong>
                    <div style="font-size:11px; color:#64748b;">${c.reporter_type} • ${c.created_at ? c.created_at.slice(0, 16) : ''}</div>
                </td>
                <td><span class="badge ${sevClass}">${c.severity}</span></td>
                <td>
                    <div style="max-width: 220px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 12px;">
                        ${c.location_address || c.landmark || 'GPS Pinpointed'}
                    </div>
                </td>
                <td>
                    <span class="badge ${statusClass}">${c.status}</span>
                    ${escBadge}
                </td>
                <td>
                    <button class="btn btn-secondary btn-sm" onclick="openComplaintModal('${c.complaint_id}')">
                        🔍 Review Case
                    </button>
                </td>
            `;
            tableBody.appendChild(tr);
        });
    } catch (e) {
        tableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; color: red;">Error: ${e.message}</td></tr>`;
    }
}

// ----------------- CASE REVIEW MODAL ----------------- //

async function openComplaintModal(complaintId) {
    activeComplaintId = complaintId;
    const modal = document.getElementById('review-modal');
    modal.classList.add('active');

    document.getElementById('modal-cid').innerText = complaintId;
    document.getElementById('modal-loading').style.display = 'block';
    document.getElementById('modal-body-content').style.display = 'none';

    try {
        const res = await fetch(`/api/complaints/${complaintId}`);
        if (!res.ok) throw new Error('Complaint not found');
        const data = await res.json();
        const c = data.complaint;
        const audit = data.audit_trail;

        // Populate photo and AI details
        document.getElementById('modal-img').src = `/${c.image_path}`;
        document.getElementById('modal-cat').innerText = c.primary_category;
        
        const sevEl = document.getElementById('modal-sev');
        sevEl.className = `badge badge-severity-${(c.severity || 'medium').toLowerCase()}`;
        sevEl.innerText = c.severity + ' Severity';
        
        document.getElementById('modal-conf').innerText = `${Math.round((c.confidence_score || 0.85) * 100)}% Confidence`;
        document.getElementById('modal-risk').innerText = c.risk_assessment || 'Standard observation.';
        document.getElementById('modal-impact').innerText = c.environmental_impact || 'Localized ecological disturbance.';
        document.getElementById('modal-action-rec').innerText = c.recommended_action || 'Sanitary unit dispatch.';

        document.getElementById('modal-reporter').innerText = `${c.reporter_type} - ${c.reporter_name || 'Anonymous'}`;
        document.getElementById('modal-coords').innerText = `${c.latitude.toFixed(5)}, ${c.longitude.toFixed(5)}`;
        document.getElementById('modal-address').innerText = c.location_address || 'N/A';
        document.getElementById('modal-time').innerText = c.created_at;

        // Reporter Citizen Description
        const descBox = document.getElementById('modal-citizen-desc');
        if (descBox) {
            descBox.innerText = c.description || 'No additional citizen notes provided.';
        }

        // Controls
        const statusSelect = document.getElementById('modal-status-select');
        if (statusSelect) {
            statusSelect.value = c.status;
        }
        document.getElementById('modal-notes').value = c.inspection_notes || '';
        document.getElementById('modal-action-taken').value = c.action_taken_notes || '';
        document.getElementById('modal-dept').innerText = c.assigned_department;
        document.getElementById('modal-officer').innerText = c.assigned_officer;

        // Escalation indicator
        const escNotice = document.getElementById('modal-esc-notice');
        if (c.escalation_level > 0 || c.status === 'Escalated' || c.status === 'Overdue') {
            escNotice.style.display = 'block';
            escNotice.innerHTML = `<strong>⚠️ ESCALATION LEVEL ${c.escalation_level || 1}:</strong> Forwarded to ${c.escalated_to || 'Zonal Municipal Commissioner'} due to SLA deadline expiration.`;
        } else {
            escNotice.style.display = 'none';
        }

        // Render Audit Timeline
        renderAuditTimeline(audit);

        // PDF Button
        document.getElementById('modal-pdf-btn').onclick = () => {
            window.open(`/api/complaints/${complaintId}/generate-pdf`, '_blank');
        };

        // Simulate Escalation Button
        document.getElementById('modal-simulate-esc-btn').onclick = () => {
            simulateEscalationForCase(complaintId);
        };

        document.getElementById('modal-loading').style.display = 'none';
        document.getElementById('modal-body-content').style.display = 'block';

    } catch (e) {
        showToast('Error loading details: ' + e.message, 'danger');
        closeComplaintModal();
    }
}

function renderAuditTimeline(audit) {
    const container = document.getElementById('modal-timeline');
    if (!container) return;
    container.innerHTML = '';

    (audit || []).forEach(item => {
        const div = document.createElement('div');
        div.className = 'timeline-item';
        div.innerHTML = `
            <div class="timeline-dot"></div>
            <div class="timeline-content">
                <div class="timeline-time">${item.timestamp} • By <strong>${item.performed_by}</strong></div>
                <div class="timeline-title">${item.action}</div>
                <div class="timeline-desc">${item.details || ''}</div>
            </div>
        `;
        container.appendChild(div);
    });
}

async function saveOfficerUpdates() {
    if (!activeComplaintId) return;

    const btn = document.getElementById('modal-save-btn');
    btn.disabled = true;
    btn.innerHTML = '⏳ Recording Official Verification...';

    const status = document.getElementById('modal-status-select').value;
    const notes = document.getElementById('modal-notes').value;
    const actionTaken = document.getElementById('modal-action-taken').value;
    
    const user = getOfficerUser();
    const officerName = user ? `${user.full_name} (${user.role.toUpperCase()})` : 'Inspecting Field Officer';

    const formData = new FormData();
    formData.append('status', status);
    formData.append('inspection_notes', notes);
    formData.append('action_taken_notes', actionTaken);
    formData.append('officer_name', officerName);

    try {
        const res = await fetch(`/api/complaints/${activeComplaintId}/update-status`, {
            method: 'POST',
            body: formData
        });

        if (!res.ok) throw new Error('Failed to update status');

        showToast('Official status and inspection audit record updated successfully.', 'success');
        await openComplaintModal(activeComplaintId);
        await loadOfficerDashboard();

    } catch (e) {
        showToast('Error saving update: ' + e.message, 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '💾 Save Inspection & Status Updates';
    }
}

async function simulateEscalationForCase(complaintId) {
    const btn = document.getElementById('modal-simulate-esc-btn');
    btn.disabled = true;
    btn.innerHTML = '⚡ Simulating SLA Delay...';

    try {
        const res = await fetch(`/api/escalation/simulate/${complaintId}`, {
            method: 'POST'
        });

        if (!res.ok) throw new Error('Simulation failed');
        const data = await res.json();

        showToast(`Escalation triggered! New Status: ${data.new_status} (Level ${data.new_level})`, 'warning');
        await openComplaintModal(complaintId);
        await loadOfficerDashboard();

    } catch (e) {
        showToast('Escalation error: ' + e.message, 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '⚡ Test SLA Escalation (+24h / +48h Demo)';
    }
}

async function triggerEscalationBatch() {
    showToast('Running background SLA verification scan across all active complaints...', 'info');
    try {
        const res = await fetch('/api/escalation/process', { method: 'POST' });
        if (!res.ok) throw new Error('SLA scan failed');
        const data = await res.json();
        
        if (data.processed_count > 0) {
            showToast(`SLA Engine Processed: ${data.processed_count} escalation/reminder event(s) triggered!`, 'warning');
        } else {
            showToast('SLA Scan Complete: All active complaints are currently within SLA deadlines.', 'success');
        }
        await loadOfficerDashboard();
    } catch (e) {
        showToast('Error during SLA scan: ' + e.message, 'danger');
    }
}

function closeComplaintModal() {
    document.getElementById('review-modal').classList.remove('active');
    activeComplaintId = null;
}

// ----------------- DOM READY INITIALIZER ----------------- //

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('officer-login-form');
    if (loginForm) loginForm.addEventListener('submit', handleOfficerLogin);

    const filterStatus = document.getElementById('filter-status');
    const filterCategory = document.getElementById('filter-category');

    if (filterStatus) filterStatus.addEventListener('change', loadComplaintsTable);
    if (filterCategory) filterCategory.addEventListener('change', loadComplaintsTable);

    const closeBtn = document.getElementById('modal-close-btn');
    if (closeBtn) closeBtn.addEventListener('click', closeComplaintModal);

    const saveBtn = document.getElementById('modal-save-btn');
    if (saveBtn) saveBtn.addEventListener('click', saveOfficerUpdates);
});
