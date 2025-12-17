# 🎯 PhonePe

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A powerful tool to catch online scammers who request QR codes. Disguised as a PhonePe payment interface, it silently captures burst photos, IP addresses, and precise location data of scammers.

Developed by surajorg. Use only against confirmed scam suspects. Do not misuse this tool.

## ⚠️ Legal Disclaimer

**Use responsibly and ethically:**
- Only target confirmed scammers
- Do not misuse this tool. Never target innocent individuals
- Check local laws regarding digital evidence collection
- This tool captures personal data and photos
- Report evidence to appropriate authorities

## ✨ Features

- 🎭 **Perfect Disguise** - Looks exactly like real PhonePe interface
- 📸 **Silent Burst Capture** - Captures 5 photos: 2 immediate, 2 mid-session, and 1 final
- 🌍 **Precise Location** - Server-side IP geolocation (City, Region, Country)
- 📱 **Device Intelligence** - Captures device info, screen resolution, timezone
- 🔒 **Secure Setup** - No exposed API keys or sensitive data
- 🖥️ **Cross-Platform** - Works on Windows, macOS, and Linux
- 🌐 **Public Tunneling** - ngrok integration for external access
- 🗂️ **Session Folders** - Per-session directories with initial/middle/final bursts, plus leftover handling for interrupted sessions
- 🧪 **Test Mode** - Built-in testing endpoint for location verification

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** installed
- **Internet connection** for geolocation and tunneling
- **ngrok account** (free) for public URLs

### Installation & Setup

1. **Clone or download** this repository

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup ngrok**
   - Get your auth token from: https://dashboard.ngrok.com/get-started/your-authtoken
   - Configure ngrok with your token:
   ```bash
   ngrok config add-authtoken YOUR_TOKEN
   ```

4. **Run the application**
   ```bash
   python3 app.py
   ```

5. **Get Public URL**
   - Copy the ngrok URL from the console output
   - Send to scammers: `"Please share your UPI QR code here: [URL]"`

## 🧪 Testing

### Test Geolocation
Visit: `http://localhost:8080/test-external`

Enter any public IP address to see location resolution:
- `8.8.8.8` - Google DNS (USA)
- `157.240.1.35` - Facebook (USA)
- `208.67.222.222` - OpenDNS (USA)

### Real Testing
1. Share your ngrok URL with someone else
2. They access it → sees PhonePe interface
3. Clicks "Share QR Code" → camera opens
4. Photo captured automatically with location data

## 📁 File Structure

```
phonepe/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── captured_photos/       # Auto-created photo storage
├── static/
│   ├── script.js         # Frontend JavaScript
│   └── styles.css        # PhonePe-like styling
└── templates/
    └── index.html        # Main scam interface
```

## 📊 Captured Data

Photos are saved per session under `captured_photos/<session_id>/` with subfolders:
- `initial/` – 2 immediate photos
- `middle/` – 2 mid-session photos
- `final/` – 1 final photo

Each session contains `session_info.json` summarizing the capture. Interrupted sessions are moved to `captured_photos/leftover_data/<session_id>/`.

Example `session_info.json`:
```json
{
  "session_id": "sess_ab12cd34ef56",
  "finalized_at": "2025-12-17T12:34:56.789Z",
  "completed": true,
  "counts": { "initial": 2, "middle": 2, "final": 1, "total": 5 },
  "ip_address": "1.2.3.4",
  "resolved_location": "Mumbai, Maharashtra, India",
  "client_geo": {
    "latitude": 12.34,
    "longitude": 56.78,
    "accuracy_meters": 20,
    "maps_url": "https://www.google.com/maps?q=12.34,56.78"
  },
  "user_agent": "Mozilla/5.0...",
  "screen_resolution": "1920x1080",
  "timezone": "Asia/Kolkata",
  "platform": "Win32"
}
```

Note: `captured_photos/` (including `leftover_data/`) is ignored by `.gitignore` and will not be pushed to GitHub.

## 📦 Dependencies

The application requires the following Python packages:
- **Flask** - Web framework
- **Requests** - HTTP library for geolocation
- **pyngrok** - ngrok Python wrapper

All dependencies are listed in `requirements.txt` and installed via:
```bash
pip install -r requirements.txt
```

You'll also need to install ngrok separately:
- **macOS**: `brew install ngrok/ngrok/ngrok`
- **Windows**: `choco install ngrok` or download from [ngrok.com](https://ngrok.com/download)
- **Linux**: `snap install ngrok`

## 🔧 Configuration

### Port Settings
Edit `app.py` line 30:
```python
PORT = 8080  # Change if port is busy
```

### Photo Directory
Edit `app.py` line 30:
```python
PHOTOS_DIR = 'captured_photos'  # Relative path
```

## 🐛 Troubleshooting

### ❌ "Port 8080 already in use"
- Kill existing processes:
  ```bash
  # macOS/Linux
  lsof -ti :8080 | xargs kill -9

  # Windows
  netstat -ano | findstr :8080
  taskkill /PID <PID> /F
  ```

### ❌ "ngrok not authenticated"
- Get new token: https://dashboard.ngrok.com/get-started/your-authtoken
- Set token: `ngrok config add-authtoken YOUR_NEW_TOKEN`

### ❌ Camera not working
- Allow camera permissions in browser
- Try refreshing the page
- Test in different browser

### ❌ Python package installation fails
```bash
# Try with specific flags
pip install --user flask requests pyngrok
# or
python -m pip install flask requests pyngrok
```


## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License © 2025 Surajorg. See the [LICENSE](LICENSE) file for details.

## ⚖️ Legal Notice

This tool is for educational and defensive purposes only. Users are responsible for complying with all applicable laws and regulations regarding digital surveillance, data collection, and evidence gathering in their jurisdiction.

---

**Happy Hunting!** 🎣📱

*Report scammers, don't become one.*
