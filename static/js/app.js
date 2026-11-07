// ECOGUARD AI - Core Application Script, PWA Engine & Navigation Controller

let cameraStream = null;
let deferredInstallPrompt = null;

// ==========================================================================
// 1. PWA SERVICE WORKER & INSTALL PROMPT HANDLERS
// ==========================================================================

// Register Service Worker
function registerServiceWorker() {
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/sw.js', { scope: '/' })
                .then((registration) => {
                    console.log('🌿 EcoGuard PWA Service Worker registered with scope:', registration.scope);
                })
                .catch((error) => {
                    console.warn('Service Worker registration failed:', error);
                });
        });
    }
}

// Listen for Android Chrome / PWA install prompt
window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent the default mini-infobar or automatic prompt
    e.preventDefault();
    deferredInstallPrompt = e;

    // Show Install App buttons in navigation bar and mobile banner
    const navInstallBtn = document.getElementById('btn-install-app');
    const pwaBanner = document.getElementById('pwa-install-banner');

    if (navInstallBtn) {
        navInstallBtn.style.display = 'inline-flex';
    }

    // Show banner on mobile devices if user hasn't dismissed it this session
    const isDismissed = sessionStorage.getItem('pwa_banner_dismissed');
    if (pwaBanner && !isDismissed) {
        pwaBanner.style.display = 'flex';
    }
});

// Trigger PWA installation
async function promptPwaInstall() {
    if (!deferredInstallPrompt) {
        showToast('To install ECOGUARD AI on Android: tap the 3 dots (⋮) in Chrome and select "Install app" or "Add to Home screen".', 'info');
        return;
    }

    // Show native Android install prompt
    deferredInstallPrompt.prompt();

    const { outcome } = await deferredInstallPrompt.userChoice;
    console.log(`User response to install prompt: ${outcome}`);

    if (outcome === 'accepted') {
        showToast('Thank you for installing ECOGUARD AI!', 'success');
    }

    // Clear prompt and hide buttons
    deferredInstallPrompt = null;
    const navInstallBtn = document.getElementById('btn-install-app');
    const pwaBanner = document.getElementById('pwa-install-banner');
    if (navInstallBtn) navInstallBtn.style.display = 'none';
    if (pwaBanner) pwaBanner.style.display = 'none';
}

// App installed event
window.addEventListener('appinstalled', (evt) => {
    console.log('ECOGUARD AI was installed successfully.');
    showToast('🎉 ECOGUARD AI added to Home Screen!', 'success');
    const navInstallBtn = document.getElementById('btn-install-app');
    const pwaBanner = document.getElementById('pwa-install-banner');
    if (navInstallBtn) navInstallBtn.style.display = 'none';
    if (pwaBanner) pwaBanner.style.display = 'none';
});

// Online / Offline Status Listeners
window.addEventListener('online', () => {
    const banner = document.getElementById('offline-indicator-banner');
    if (banner) banner.style.display = 'none';
    showToast('🌐 Internet connection restored. Cloud AI vision active.', 'success');
});

window.addEventListener('offline', () => {
    const banner = document.getElementById('offline-indicator-banner');
    if (banner) banner.style.display = 'block';
    showToast('📡 You are offline. Operating with local device cache.', 'warning');
});

// ==========================================================================
// 2. TAB NAVIGATION & VIEW CONTROLLER
// ==========================================================================

function showTab(tabId) {
    // Hide all tab panes
    document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));

    // Deactivate top nav buttons
    document.querySelectorAll('.nav-tab-btn').forEach(el => el.classList.remove('active'));

    // Deactivate mobile bottom nav buttons
    document.querySelectorAll('.mobile-nav-btn').forEach(el => el.classList.remove('active'));

    // Show target tab pane
    const target = document.getElementById(tabId);
    if (target) {
        target.classList.add('active');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Activate matching top nav button
    const topBtn = document.querySelector(`.nav-tab-btn[data-tab="${tabId}"]`);
    if (topBtn) {
        topBtn.classList.add('active');
    }

    // Activate matching mobile bottom nav button
    const mobileBtn = document.querySelector(`.mobile-nav-btn[data-tab="${tabId}"]`);
    if (mobileBtn) {
        mobileBtn.classList.add('active');
    }

    // Trigger tab-specific map refits and data fetching
    if (tabId === 'tab-report') {
        if (window.pickerMap) {
            setTimeout(() => { window.pickerMap.invalidateSize(); }, 250);
        }
    }
    if (tabId === 'tab-hotspots') {
        if (window.hotspotMap) {
            setTimeout(() => { 
                window.hotspotMap.invalidateSize(); 
                if (typeof loadHotspotsData === 'function') loadHotspotsData();
            }, 250);
        }
    }
    if (tabId === 'tab-citizen') {
        if (typeof loadCitizenDashboard === 'function') {
            loadCitizenDashboard();
        }
    }
    if (tabId === 'tab-officer') {
        if (typeof checkOfficerAuthAndRender === 'function') {
            checkOfficerAuthAndRender();
        }
    }
    if (tabId === 'tab-knowledge') {
        if (typeof loadKnowledgeBase === 'function') {
            loadKnowledgeBase();
        }
    }
}

// Toast Notifications
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'danger') icon = '⚠️';
    if (type === 'warning') icon = '⚡';

    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4500);
}

// ==========================================================================
// 3. OFFICER AUTH STATE MANAGEMENT
// ==========================================================================

function getOfficerToken() {
    return localStorage.getItem('ecoguard_officer_token');
}

function getOfficerUser() {
    const u = localStorage.getItem('ecoguard_officer_user');
    return u ? JSON.parse(u) : null;
}

function setOfficerAuth(token, user) {
    localStorage.setItem('ecoguard_officer_token', token);
    localStorage.setItem('ecoguard_officer_user', JSON.stringify(user));
    updateAuthUi();
}

function clearOfficerAuth() {
    localStorage.removeItem('ecoguard_officer_token');
    localStorage.removeItem('ecoguard_officer_user');
    updateAuthUi();
}

function updateAuthUi() {
    const user = getOfficerUser();
    const badgeContainer = document.getElementById('nav-user-badge-container');
    if (!badgeContainer) return;

    if (user) {
        badgeContainer.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px;">
                <span class="user-badge" title="${user.department}">
                    🛡️ ${user.full_name} (${user.role.toUpperCase()})
                </span>
                <button class="btn btn-secondary btn-sm" onclick="logoutOfficer()" title="Log out from officer account">
                    Log Out
                </button>
            </div>
        `;
    } else {
        badgeContainer.innerHTML = `
            <button class="btn btn-secondary btn-sm" onclick="showTab('tab-officer')">
                🛡️ Officer Login
            </button>
        `;
    }
}

function logoutOfficer() {
    clearOfficerAuth();
    showToast('Logged out successfully.', 'info');
    if (typeof checkOfficerAuthAndRender === 'function') {
        checkOfficerAuthAndRender();
    }
}

// ==========================================================================
// 4. CAMERA CAPTURE (MOBILE NATIVE + DESKTOP WEBRTC)
// ==========================================================================

function handleCameraTrigger() {
    // Detect mobile touch device: on Android / iOS, native file capture is faster and full-resolution
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || (window.innerWidth <= 768 && ('ontouchstart' in window));
    const mobileCameraInput = document.getElementById('camera-file-input');

    if (isMobile && mobileCameraInput) {
        mobileCameraInput.click();
    } else {
        openCameraModal();
    }
}

async function openCameraModal() {
    const modal = document.getElementById('camera-modal');
    const video = document.getElementById('camera-video');

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        // Fall back to mobile camera file input if getUserMedia unavailable
        const mobileCameraInput = document.getElementById('camera-file-input');
        if (mobileCameraInput) {
            mobileCameraInput.click();
            return;
        }
        showToast('Camera capture requires HTTPS or browser permission.', 'danger');
        return;
    }

    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } },
            audio: false
        });
        video.srcObject = cameraStream;
        await video.play();
        modal.classList.add('active');
    } catch (err) {
        // Fall back to file input if camera access blocked
        const mobileCameraInput = document.getElementById('camera-file-input');
        if (mobileCameraInput) {
            mobileCameraInput.click();
            return;
        }
        showToast('Camera access denied or unavailable: ' + err.message, 'danger');
    }
}

function closeCameraModal() {
    const modal = document.getElementById('camera-modal');
    if (modal) modal.classList.remove('active');
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
}

function snapPhotoFromCamera() {
    const video = document.getElementById('camera-video');
    const canvas = document.getElementById('camera-canvas');
    if (!video || !canvas) return;

    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
        if (!blob) {
            showToast('Failed to snapshot camera image.', 'danger');
            return;
        }
        const file = new File([blob], `camera_dump_${Date.now()}.jpg`, { type: 'image/jpeg' });
        closeCameraModal();
        if (typeof handleImageSelected === 'function') {
            handleImageSelected(file);
            showToast('Photograph captured and dispatched for AI pre-scan!', 'success');
        }
    }, 'image/jpeg', 0.92);
}

// Check System Status on Load
async function checkSystemStatus() {
    try {
        const res = await fetch('/api/system/status');
        if (res.ok) {
            const data = await res.json();
            const badge = document.getElementById('ai-engine-status-badge');
            if (badge) {
                if (data.gemini_configured) {
                    badge.innerHTML = '⚡ Gemini Vision Active';
                    badge.className = 'badge badge-action';
                } else {
                    badge.innerHTML = '🌱 Ecological Heuristic Mode';
                    badge.className = 'badge badge-acknowledged';
                    badge.title = 'Add GEMINI_API_KEY in .env for direct Gemini Cloud Vision';
                }
            }
        }
    } catch (e) {
        // Offline or connection failure
    }
}

// ==========================================================================
// 5. APPLICATION INITIALIZER
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    // 1. Register PWA Service Worker
    registerServiceWorker();

    // 2. Top Nav Tab Buttons
    document.querySelectorAll('.nav-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            showTab(tabId);
            window.location.hash = tabId.replace('tab-', '');
        });
    });

    // 3. Mobile Bottom Nav Buttons
    document.querySelectorAll('.mobile-nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            showTab(tabId);
            window.location.hash = tabId.replace('tab-', '');
        });
    });

    // 4. Initial Hash Routing
    const hash = window.location.hash.replace('#', '');
    if (hash && document.getElementById(`tab-${hash}`)) {
        showTab(`tab-${hash}`);
    } else {
        showTab('tab-home');
    }

    updateAuthUi();
    checkSystemStatus();

    // 5. PWA Install Buttons & Banner actions
    const navInstallBtn = document.getElementById('btn-install-app');
    if (navInstallBtn) navInstallBtn.addEventListener('click', promptPwaInstall);

    const bannerInstallBtn = document.getElementById('btn-banner-install');
    if (bannerInstallBtn) bannerInstallBtn.addEventListener('click', promptPwaInstall);

    const bannerDismissBtn = document.getElementById('btn-banner-dismiss');
    if (bannerDismissBtn) {
        bannerDismissBtn.addEventListener('click', () => {
            const pwaBanner = document.getElementById('pwa-install-banner');
            if (pwaBanner) pwaBanner.style.display = 'none';
            sessionStorage.setItem('pwa_banner_dismissed', 'true');
        });
    }

    // 6. Camera Buttons
    const openCamBtn = document.getElementById('btn-open-camera');
    if (openCamBtn) openCamBtn.addEventListener('click', handleCameraTrigger);

    const browseFileBtn = document.getElementById('btn-browse-file');
    const wasteFileInput = document.getElementById('waste-file-input');
    if (browseFileBtn && wasteFileInput) {
        browseFileBtn.addEventListener('click', () => wasteFileInput.click());
    }

    const closeCamBtn = document.getElementById('btn-close-camera');
    if (closeCamBtn) closeCamBtn.addEventListener('click', closeCameraModal);

    const snapCamBtn = document.getElementById('btn-snap-camera');
    if (snapCamBtn) snapCamBtn.addEventListener('click', snapPhotoFromCamera);

    // 7. Check if already launched in standalone PWA mode
    if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true) {
        console.log('Running in standalone PWA mode');
        const navInstallBtn = document.getElementById('btn-install-app');
        const pwaBanner = document.getElementById('pwa-install-banner');
        if (navInstallBtn) navInstallBtn.style.display = 'none';
        if (pwaBanner) pwaBanner.style.display = 'none';
    }
});
