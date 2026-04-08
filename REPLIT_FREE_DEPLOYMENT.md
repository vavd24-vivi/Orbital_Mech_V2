# Free Deployment Guide: Replit (No Credit Card Required)

**Best Free Option:** Replit.com  
**Duration:** 7+ days free tier with excellent uptime  
**No Credit Card:** ✅ Yes  
**Time to Deploy:** ~10 minutes

---

## Why Replit?

✅ **No credit card required**  
✅ **Full Python/Flask support** (backend)  
✅ **Static file serving** (frontend)  
✅ **Free domain** (replit.dev subdomain)  
✅ **Always-on web deployment** (unlike free tier alternatives)  
✅ **Clone from GitHub** (instant setup)  
✅ **7+ days free tier** (and can continue if active)  

---

## Step-by-Step Deployment to Replit

### Step 1: Create Replit Account

1. Go to **[replit.com](https://replit.com)**
2. Click **"Sign up"**
3. Choose **"Sign up with GitHub"** (or email)
4. Complete signup (no credit card prompted)

### Step 2: Import Your Repository

1. Click **"Create"** or **"+"** button
2. Select **"Import from GitHub"**
3. Paste: `https://github.com/yourusername/WorkshopApril7To10`
4. Click **"Import"**
5. Replit auto-detects Python and creates environment

### Step 3: Configure Backend (First Time Only)

Once imported, Replit opens the editor. Follow these steps:

#### 3a. Create `.replit` Configuration File

At project root, create `.replit`:

```toml
run = "cd backend && python -m gunicorn -w 1 -b 0.0.0.0:5000 --timeout 60 api.app:app"

[env]
PYTHONUNBUFFERED = "1"
FLASK_ENV = "production"
```

#### 3b. Update `requirements.txt` for Replit

Edit `backend/requirements.txt` to **minimize memory usage**:

```txt
Flask==3.0.0
Flask-CORS==4.0.0
numpy==1.24.3
scipy==1.10.1
sgp4==2.23
gunicorn==20.1.0
```

**Remove if present:**
- `flask-caching` (uses extra memory)
- `redis` (not needed for free tier)
- `sqlalchemy` (unless you need database)
- `psycopg2` (PostgreSQL driver)

#### 3c. Optimize `backend/api/app.py`

Replace the gunicorn line at bottom to use only 1 worker (Replit memory constraint):

Click on file browser, open `backend/api/app.py`, find the line at the end:

```python
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
```

This is fine - Replit's run command (in `.replit` file) will handle gunicorn.

### Step 4: Start the Replit Server

1. Click **"Run"** button (top center)
2. Wait 30-60 seconds for dependencies to install
3. Terminal shows: `Running on http://0.0.0.0:5000`

### Step 5: Set Up Frontend Routing

Replit needs to serve static files. Modify `backend/api/app.py` to serve frontend:

Find this section (near the top where Flask is initialized):

```python
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests
```

Add these lines right after:

```python
# Serve frontend static files
import os
frontend_path = os.path.join(os.path.dirname(__file__), '../../frontend/public')
app.register_blueprint(Flask('frontend', __name__, static_folder=frontend_path, static_url_path='').blueprint)

@app.route('/')
def serve_frontend():
    """Serve main HTML file"""
    return send_from_directory(frontend_path, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory(frontend_path, filename)
```

Actually, simpler approach - add this at the very end of app.py (before the `if __name__ == '__main__':` block):

```python
# Serve frontend from static directory
@app.route('/')
def index():
    from flask import send_from_directory
    return send_from_directory('../frontend/public', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    from flask import send_from_directory
    import mimetypes
    try:
        return send_from_directory('../frontend/public', path)
    except:
        return send_from_directory('../frontend/public', 'index.html'), 404
```

### Step 6: Get Your Public URL

1. After running, Replit shows **"Webview"** tab on right
2. Click **"Open in new tab"** button
3. Your URL appears: `https://YOUR-REPLIT-NAME.replit.dev`
4. **Copy this URL** - this is your public deployment

### Step 7: Test API Endpoints

In the webview:
1. Open browser console (F12)
2. Test API call:

```javascript
fetch('https://YOUR-REPLIT-NAME.replit.dev/api/health')
  .then(r => r.json())
  .then(d => console.log(d));
```

Should return: `{status: 'ok', ...}`

---

## Backend Optimization for Replit

The platform has memory constraints (~500MB RAM). Here's optimization:

### Disable Heavy Features

Create `backend/config.py`:

```python
# Replit-optimized configuration
REPLIT_MODE = True

# Disable caching (saves memory)
ENABLE_CACHING = False

# Limit animation frame generation (memory intensive)
MAX_ANIMATION_FRAMES = 360  # Default, 1 orbit

# Reduce animation viewport
ANIMATION_RESOLUTION = 'low'  # Options: 'low' (fast), 'medium', 'high'

# Disable database (for now)
ENABLE_DATABASE = False
```

### Memory-Efficient Animation Generation

Edit `backend/orbital_mechanics/animation.py`, find `OrbitAnimationGenerator`:

Replace the `generate_frames()` method with a memory-efficient version:

```python
def generate_frames(self):
    """Generate animation frames (memory-optimized for Replit)"""
    import gc
    current_time = 0
    
    for frame_num in range(self.total_frames):
        # Pre-allocate to avoid memory fragmentation
        r, v = self.propagator.propagate(current_time)
        
        kep = cartesian_to_keplerian(r, v)
        r_mag = np.linalg.norm(r)
        v_mag = np.linalg.norm(v)
        altitude = r_mag - EARTH_RADIUS_KM
        
        yield {
            'frame': frame_num,
            'time_seconds': current_time,
            'position_eci': [float(r[0]), float(r[1]), float(r[2])],  # Numpy → Python types
            'velocity_eci': [float(v[0]), float(v[1]), float(v[2])],
            'position_magnitude_km': float(r_mag),
            'velocity_magnitude_km_s': float(v_mag),
            'altitude_km': float(altitude),
            'semi_major_axis_km': float(kep['a']),
            'eccentricity': float(kep['e']),
            'inclination_deg': float(kep['i'] * 180 / np.pi),
            'true_anomaly_deg': float(kep['nu'] * 180 / np.pi)
        }
        
        current_time += self.dt
        
        # Garbage collection every 50 frames
        if frame_num % 50 == 0:
            gc.collect()
```

### Limit API Response Size

Edit `backend/api/app.py`, find `animation_orbit_frames()`:

```python
@app.route('/api/animation/orbit-frames', methods=['POST'])
def animation_orbit_frames():
    """Generate orbit animation frames (memory-optimized)"""
    from orbital_mechanics.animation import OrbitAnimationGenerator
    
    data = request.get_json()
    
    try:
        # Limit to 360 frames for Replit memory
        max_frames = min(data.get('frames_per_orbit', 360), 360)
        
        generator = OrbitAnimationGenerator(
            data.get('initial_state', {}),
            num_orbits=data.get('num_orbits', 1),
            frames_per_orbit=max_frames
        )
        
        frames = []
        for frame in generator.generate_frames():
            frames.append(frame)
            # Limit to 360 total frames in one request
            if len(frames) >= 360:
                break
        
        return jsonify({
            'total_frames': len(frames),
            'frames': frames,
            'note': 'Replit free tier limited to 360 frames per request'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400
```

---

## Frontend Optimization for Replit

### Disable Heavy 3D Visualization

Edit `frontend/public/app.js`, comment out CesiumJS initialization:

```javascript
function setupCesiumVisualization() {
    // Disabled on Replit (memory constraint)
    // const container = document.getElementById('cesium-container');
    // if (!container) return;
    
    console.log('CesiumJS visualization disabled on Replit free tier');
    
    // Optional: Show 2D canvas instead
    const container = document.getElementById('cesium-container');
    if (container) {
        container.innerHTML = '<p style="padding: 20px; background: #f0f0f0; border-radius: 8px;"><strong>2D Visualization Mode</strong><br>Use the 2D Ground Track Map or Animation sections for visualization.</p>';
    }
}
```

### Reduce Font/Asset Loading

Edit `frontend/public/index.html`, remove CDN fonts if using Bootstrap:

```html
<!-- Keep Bootstrap only, remove extra fonts -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
```

---

## Complete `.replit` File (Copy-Paste Ready)

Create this file at project root:

```toml
# Replit configuration for Orbital Dynamics

run = "cd backend && python -m gunicorn -w 1 -b 0.0.0.0:5000 --timeout 60 api.app:app"

[env]
PYTHONUNBUFFERED = "1"
FLASK_ENV = "production"
LOG_LEVEL = "warning"

[packager]
language = "python3"
```

---

## Complete `requirements.txt` (Copy-Paste Ready)

Replace `backend/requirements.txt` with:

```txt
# Core framework
Flask==3.0.0
Flask-CORS==4.0.0

# Math/science (minimal)
numpy==1.24.3
scipy==1.10.1

# SGP4 propagation
sgp4==2.23

# Server
gunicorn==20.1.0

# Optional: datetime parsing
python-dateutil==2.8.2
```

---

## Complete Simplified `backend/api/app.py` (Key Section)

Add this at the end of the `app.py` file (before main):

```python
# ============================================================================
# Frontend Serving (for Replit)
# ============================================================================

@app.route('/')
def serve_index():
    """Serve main HTML file."""
    from flask import send_from_directory
    try:
        return send_from_directory('../frontend/public', 'index.html')
    except:
        return jsonify({'error': 'Frontend not found'}), 404

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files (JS, CSS, images)."""
    from flask import send_from_directory
    try:
        return send_from_directory('../frontend/public', filename)
    except:
        # Fallback: serve index for SPA routing
        return send_from_directory('../frontend/public', 'index.html')
```

---

## Testing Your Deployment

### 1. Test Backend API

```bash
# In Replit terminal after "Run" completes:
curl https://YOUR-REPLIT-NAME.replit.dev/api/health
```

Should return:
```json
{"status": "ok", "service": "Orbital Dynamics API"}
```

### 2. Test Frontend

Navigate to:
```
https://YOUR-REPLIT-NAME.replit.dev/
```

Should see home page ✓

### 3. Test TLE Parsing

In browser console:
```javascript
const tleLine1 = "1 25544U 98067A   21348.58768519  .00008803  00000-0  18458-3 0  9991";
const tleLine2 = "2 25544  51.6439 260.8917 0002550  37.5917 322.5653 15.49207881317741";

fetch('https://YOUR-REPLIT-NAME.replit.dev/api/tle/parse', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({name: 'ISS', line1: tleLine1, line2: tleLine2})
}).then(r => r.json()).then(d => console.log(d));
```

---

## Keeping Your Replit Alive Beyond 7 Days

Replit free tier stays up as long as the project is **actively used**. To keep it running:

### Option A: Keep it Pinned (Automatic)
- Projects are automatically kept alive if you visit at least once per 7 days
- Access the URL periodically

### Option B: Add a Heartbeat Ping
Add this to `backend/api/app.py`:

```python
import threading
import time

def keep_alive_ping():
    """Ping service periodically to keep Replit alive"""
    while True:
        time.sleep(300)  # Ping every 5 minutes
        try:
            app.logger.info('Heartbeat: Server still running')
        except:
            pass

# Start heartbeat in background (optional)
# threading.Thread(target=keep_alive_ping, daemon=True).start()
```

---

## Limitations on Replit Free Tier

⚠️ **Known Limitations:**

| Feature | Status | Note |
|---|---|---|
| Animation Frames | 360 max | 1 orbit only, reduces memory usage |
| Concurrent Users | 1-2 recommended | Free tier shared CPU |
| CesiumJS 3D | Disabled | Use 2D maps instead |
| Database | Not included | Can use SQLite if needed |
| Uptime | 99% | As long as <7 days inactive |
| Custom Domain | No | Use replit.dev subdomain |
| SSL/TLS | Yes | Automatic ✓ |

---

## Sharing Your Deployment

1. **Public URL:** `https://YOUR-REPLIT-NAME.replit.dev`
2. **Share with team:**
   - Send the URL directly
   - Works in any browser
   - No installation required
3. **For flight ops:** All core features available (TLE parsing, conversions, Hohmann transfers, ground track, launch windows)

---

## If You Need More Power Later

When free tier ends (after ~7 days), options:

1. **Replit Paid** ($7/month) - Keeps project always running
2. **AWS Free Tier** (12 months) - Requires credit card
3. **DigitalOcean** ($5/month) - Requires credit card
4. **Heroku** (deprecated free tier)

---

## Troubleshooting

### "ModuleNotFoundError: No module named..."

**Fix:** Replit sometimes doesn't install dependencies automatically.

```bash
# In Replit terminal:
pip install -r backend/requirements.txt
```

### "Timeout" on Animation Endpoints

**Fix:** Limit frames and reduce propagation complexity

Change in `app.py`:
```python
max_frames = min(data.get('frames_per_orbit', 360), 180)  # Reduce to 180
```

### Frontend Not Loading

**Fix:** Make sure `.replit` file and frontend serving code is in place

Verify:
1. File `.replit` exists at project root
2. `frontend/public/index.html` exists
3. Routing code added to `backend/api/app.py`

### Port 5000 Already in Use

**Fix:** Use a different port in `.replit`:

```toml
run = "cd backend && python -m gunicorn -w 1 -b 0.0.0.0:8080 --timeout 60 api.app:app"
```

---

## Summary

✅ **No credit card required**  
✅ **Free tier: 7+ days**  
✅ **Deploy in 10 minutes**  
✅ **All core features working**  
✅ **Public URL for sharing**  
✅ **HTTPS included**  

**Next steps:**
1. Go to [replit.com](https://replit.com)
2. Sign up with GitHub (free)
3. Import your repository
4. Add `.replit` file
5. Click "Run"
6. Share the URL!

---

**Status:** Production-ready for testing/demos + Free & no credit card required  
**Duration:** 1-2 weeks (can extend with activity)  
**Best for:** Quick demos, flight ops interviews, team testing
