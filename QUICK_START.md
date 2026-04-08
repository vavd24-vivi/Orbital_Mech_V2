"""
Quick Start Guide for Orbital Dynamics Website

This guide will help you get the website running locally and start exploring orbital mechanics.
"""

# Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Start the API Server
```bash
python -m api.app
```
You'll see:
```
Starting Orbital Dynamics API Server...
 * Running on http://127.0.0.1:5000/
```

### 3. Serve the Frontend
In another terminal:
```bash
cd frontend/public
python -m http.server 8000
```

### 4. Open in Browser
Navigate to: `http://localhost:8000`

---

## Using the Website

### 🛰️ TLE Understanding
1. Go to "TLE Understanding" section
2. Paste ISS TLE lines (or use default example)
3. Click "Parse TLE"
4. See orbital parameters extracted

**ISS Example TLE:**
```
ISS (ZARYA)
1 25544U 98067A   24095.50000000  .00016717  00000-0  29825-3 0  9991
2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.54851852429794
```

### 🔄 Keplerian Elements
1. Go to "Keplerian Elements" section
2. Use sliders to adjust orbital parameters
3. Watch 3D visualization update in real-time
4. See calculated state vectors

**Try these:**
- **LEO Circular**: a=6778, e=0.0, i=51.6°
- **Elliptical Transfer**: a=24471, e=0.77, i=0°
- **Molniya Orbit**: a=26600, e=0.74, i=63.4°

### ✈️ Orbit Types ("Choose Your Fighter")
1. Go to "Orbit Types" section
2. Browse all 11 orbit types with real spacecraft examples
3. Each card shows:
   - Orbital parameters
   - Common uses
   - Real satellites currently in that orbit

### 💫 Maneuvers & Transfers
1. Go to "Maneuvers & Transfers"
2. Enter initial and final orbit radii for Hohmann transfer
3. Calculate ΔV and transfer time

**Example Transfer (LEO to GEO):**
- Initial: 6,778 km (400 km altitude)
- Final: 42,164 km (geostationary)
- See required ΔV and time

### 📡 Ground Track
1. Satellite position visibility
2. Ground station access windows
3. Coming soon: Interactive 2D map

---

## API Examples

### Example 1: Parse Current ISS TLE

```bash
curl -X POST http://localhost:5000/api/tle/parse \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ISS",
    "line1": "1 25544U 98067A   24095.50000000  .00016717  00000-0  29825-3 0  9991",
    "line2": "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.54851852429794"
  }'
```

**Response:**
```json
{
  "satellite_name": "ISS",
  "catalog_number": 25544,
  "inclination_deg": 51.6416,
  "eccentricity": 0.0006703,
  "mean_motion_rpm": 15.5485,
  "period_seconds": 5525.5,
  "period_minutes": 92.1
}
```

### Example 2: Convert Keplerian to State Vectors

```bash
curl -X POST http://localhost:5000/api/conversions/keplerian-to-state \
  -H "Content-Type: application/json" \
  -d '{
    "semi_major_axis_km": 7000,
    "eccentricity": 0.0,
    "inclination_deg": 51.6,
    "raan_deg": 0.0,
    "argument_of_perigee_deg": 0.0,
    "true_anomaly_deg": 0.0
  }'
```

### Example 3: Calculate Hohmann Transfer

```bash
curl -X POST http://localhost:5000/api/maneuvers/hohmann \
  -H "Content-Type: application/json" \
  -d '{
    "r1_km": 6778,
    "r2_km": 42164
  }'
```

---

## Learning Path

### Beginner
1. Start with "Home" and "TLE Understanding"
2. Experiment with TLE parsing
3. Explore "Orbit Types"
4. Calculate a simple Hohmann transfer

### Intermediate
1. Dive into "Keplerian Elements"
2. Understand state vector conversions
3. Study different maneuvers
4. Calculate complex transfer sequences

### Advanced
1. Study "Perturbations" and J2 effects
2. Understand propagator differences
3. Analyze real satellite orbits
4. Ground track and access calculations

---

## Orbital Mechanics Refresher

### Key Concepts

**Keplerian Elements (6 parameters define an orbit):**
- **a** (Semi-major axis): Average orbital radius
- **e** (Eccentricity): Orbit shape (0=circle, <1=ellipse)
- **i** (Inclination): Orbital plane angle from equator
- **Ω** (RAAN): Ascending node position around Earth
- **ω** (Argument of Perigee): Periapsis orientation
- **ν** (True Anomaly): Satellite position in orbit

**State Vectors:**
- **r** (Position): [x, y, z] in ECI frame
- **v** (Velocity): [vx, vy, vz] in ECI frame

### Orbital Mechanics Equations

**Orbital Period:**
$$T = 2\pi\sqrt{\frac{a^3}{\mu}}$$

**Orbital Velocity:**
$$v = \sqrt{\mu\left(\frac{2}{r} - \frac{1}{a}\right)}$$

**Hohmann Transfer ΔV:**
- ΔV₁ = $v_1(r_1) - v_{\text{transfer,perigee}}$
- ΔV₂ = $v_2(r_2) - v_{\text{transfer,apogee}}$

---

## Troubleshooting

### API Server won't start
- Check port 5000 isn't in use: `netstat -an | grep 5000`
- Try different port: `python -c "app.run(port=5001)"`
- Verify Flask installed: `pip list | grep Flask`

### Frontend not connecting to API
- Check CORS is enabled in `app.py`
- Verify API server running: `curl http://localhost:5000/api/health`
- Check browser console for errors (F12)

### Missing sgp4 library
- Install: `pip install sgp4`
- Note: SGP4 is optional; app works with Two-Body propagator

### Visualization not loading
- Check CesiumJS CDN accessible
- Verify browser supports WebGL
- Try different browser (Chrome/Firefox recommended)

---

## Next Steps

1. **Dive Deeper**: Read referenced papers from Curtis (2013) and Vallado et al. (2006)
2. **Extend Code**: Add new propagators or perturbations
3. **Real Tracking**: Use live CelesTrak data for ISS tracking
4. **Visualization**: Enhance 3D orbit rendering
5. **Deploy**: Host on public server for global access

---

## Resources

- **Curtis Textbook**: https://www.elsevier.com/books/orbital-mechanics-for-engineering-students/curtis/978-0-08-102133-0
- **Vallado AIAA Paper**: https://celestrak.org/publications/AIAA/2006-6753/
- **CelesTrak**: https://celestrak.org/
- **CesiumJS**: https://cesium.com/
- **SGP4 Library**: https://pypi.org/project/sgp4/

---

### Questions?

Check the "References" section in the website for detailed citations and academic sources.

Enjoy exploring orbital mechanics! 🚀
