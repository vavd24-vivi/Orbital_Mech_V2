# 🚀 Orbital Dynamics: Interactive Educational Web Platform

An interactive educational website for learning orbital mechanics, TLE data analysis, and space mission planning. Built with **Firebase Cloud Functions** (Python 3.12) backend and **CesiumJS** for 3D visualization.

**🎉 NEW**: Now powered by Firebase with user authentication, data persistence, and global CDN distribution!

**Target Audience**: Space enthusiasts, engineering students, flight operations professionals, and anyone preparing for careers in space operations.

**Tone**: Accessible science communication  - making complex orbital mechanics engaging and understandable.

---

## 🎯 Quick Links

- **📖 Deployment Guide**: [FIREBASE_SETUP_GUIDE.md](FIREBASE_SETUP_GUIDE.md) - Step-by-step setup (5-10 minutes)
- **🏗️ Architecture**: [FIREBASE_MIGRATION_GUIDE.md](FIREBASE_MIGRATION_GUIDE.md) - Technical overview
- **📊 What's New**: [PROJECT_MODERNIZATION_REPORT.md](PROJECT_MODERNIZATION_REPORT.md) - Complete review of improvements
- **🔗 Live Demo**: [orbital-dynamics-isu.web.app](https://orbital-dynamics-isu.web.app) (deploy your own!)

---

## 📋 Table of Contents

1. [Features](#features)
2. [Project Structure](#project-structure)
3. [Getting Started](#getting-started)
4. [Deployment to Firebase](#deployment-to-firebase)
5. [API Documentation](#api-documentation)
6. [Modules & Components](#modules--components)
7. [References & Citations](#references--citations)

---

## ✨ Features

### Core Orbital Mechanics

- **TLE Understanding & Parsing**: Read, parse, and analyze Two-Line Element sets in real-time
- **State Vector Conversions**: Seamless conversion between Cartesian state vectors and Keplerian orbital elements
- **Interactive 3D Visualization**: CesiumJS-powered 3D Earth with real-time orbit visualization
- **Dynamic Orbital Element Sliders**: Adjust orbital parameters in real-time and see instant visualization updates
- **Orbit Type Catalog**: 10+ orbital types with characteristics, uses, and real spacecraft examples:
  - LEO (Low Earth Orbit)
  - GEO (Geostationary)
  - SSO (Sun-Synchronous)
  - Molniya (Highly Elliptical)
  - Tundra, Polar, Equatorial
  - Semisynchronous, Lunar, Heliocentric, and more

- **Maneuver Calculators**:
  - Hohmann Transfer (two-impulse transfer)
  - Bi-elliptic Transfer (three-impulse transfer)
  - Plane Change calculations
  - ΔV and Time of Flight computations

- **Ground Track & Access Analysis**:
  - Satellite sub-satellite point mapping
  - Access window calculations (AOS/LOS)
  - Line-of-sight visibility from ground stations
  - Custom elevation angle masking
  - Multiple map projections (Sinusoidal, Mollweide, Lambert Azimuthal)

- **Perturbation Engine**:
  - J2 oblateness perturbation effects
  - RAAN precession and apsidal advance visualization
  - Comparison: Two-Body vs J2-Perturbed orbits

- **Propagator Comparison**:
  - Two-Body Keplerian propagator
  - J2-Perturbed propagator (linearized)
  - SGP4/SDP4 (NORAD standard)
  - Accuracy and use case analysis

- **Educational Resources**: APA-formatted citations from peer-reviewed sources and authoritative references

---

## 📁 Project Structure

```
WorkshopApril7To10/
│
├── backend/                          # Python Flask API
│   ├── requirements.txt              # Python dependencies
│   ├── api/
│   │   ├── __init__.py
│   │   └── app.py                    # Flask REST API server
│   │
│   └── orbital_mechanics/            # Core orbital mechanics library
│       ├── __init__.py
│       ├── constants.py              # Physical constants and parameters
│       ├── conversions.py            # State vector ↔ Keplerian conversions
│       ├── tle.py                    # TLE parsing and handling
│       ├── propagators.py            # Propagation engines (Two-Body, J2, SGP4)
│       ├── maneuvers.py              # Orbital maneuvers & transfers
│       ├── ground_track.py           # Ground track & access calculations
│       └── orbit_catalog.py          # Orbit type database with metadata
│
└── frontend/                         # Web interface
    ├── public/
    │   ├── index.html                # Main HTML page
    │   ├── app.js                    # Frontend application logic
    │   └── styles.css                # UI styling

```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+ (for local development)
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Firebase account (free tier available at [firebase.google.com](https://firebase.google.com))
- Node.js (for Firebase CLI)

### Quick Deploy to Firebase (5 minutes)

**Most users should follow this path:**

1. **Read**: [FIREBASE_SETUP_GUIDE.md](FIREBASE_SETUP_GUIDE.md) - Complete step-by-step instructions
2. **Create**: Firebase project at [console.firebase.google.com](https://console.firebase.google.com)
3. **Deploy**: Run `firebase deploy` from project root
4. **Visit**: https://orbital-dynamics-isu.web.app

### Local Development (Optional)

If you want to develop locally before deploying:

```bash
# 1. Navigate to project directory
cd WorkshopApril7To10

# 2. Set up Python virtual environment
python -m venv venv

# Activate (Windows):
venv\Scripts\activate
# Or (macOS/Linux):
source venv/bin/activate

# 3. Install Python dependencies
cd backend
pip install -r requirements.txt

# 4. Start Flask API (for testing locally)
python -m api.app
# Server runs at http://localhost:5000

# 5. In another terminal, serve frontend
cd frontend/public
python -m http.server 8000

# 6. Open browser: http://localhost:8000
```

**Note**: Local development uses Flask. Production uses Firebase Cloud Functions.

### Deployment to Firebase

```bash
cd api
python app.py
```

The API server will start on `http://localhost:5000`

**Available endpoints:**
```
GET  /api/health                              # Health check
POST /api/tle/parse                          # Parse TLE data
POST /api/tle/info                           # Get TLE orbital info
POST /api/conversions/state-to-keplerian     # Convert state vectors
POST /api/conversions/keplerian-to-state     # Convert to state vectors
POST /api/maneuvers/hohmann                  # Calculate Hohmann transfer
POST /api/maneuvers/bielliptic              # Calculate bi-elliptic transfer
POST /api/maneuvers/plane-change            # Calculate plane change
POST /api/propagation/two-body              # Propagate with two-body model
POST /api/ground-track/horizon-distance     # Calculate horizon distance
GET  /api/orbits/list                       # List all orbit types
GET  /api/orbits/<type>                     # Get orbit details
POST /api/orbits/period                     # Calculate orbital period
```

#### 4. Serve Frontend

Option A: Simple HTTP server
```bash
cd frontend/public
python -m http.server 8000
```

Then navigate to `http://localhost:8000`

Option B: Use your preferred web server (nginx, Apache, etc.)

---

## 📡 API Documentation

### TLE Endpoints

#### Parse TLE
**POST** `/api/tle/parse`

Request:
```json
{
    "name": "ISS",
    "line1": "1 25544U 98067A   21348.58768519  .00008803  00000-0  18458-3 0  9991",
    "line2": "2 25544  51.6439 260.8917 0002550  37.5917 322.5653 15.49207881317741"
}
```

Response:
```json
{
    "satellite_name": "ISS",
    "catalog_number": 25544,
    "inclination_deg": 51.6439,
    "raan_deg": 260.8917,
    "eccentricity": 0.0002550,
    "argument_of_perigee_deg": 37.5917,
    "mean_anomaly_deg": 322.5653,
    "mean_motion_rpm": 15.49207881,
    "bstar": 0.00018458
}
```

### Conversion Endpoints

#### State Vectors to Keplerian
**POST** `/api/conversions/state-to-keplerian`

Request:
```json
{
    "position": [7000, 0, 0],
    "velocity": [0, 7.55, 0],
    "mu": 398600.4418
}
```

Response:
```json
{
    "semi_major_axis_km": 7000,
    "eccentricity": 0.0,
    "inclination_deg": 0.0,
    "raan_deg": 0.0,
    "argument_of_perigee_deg": 0.0,
    "true_anomaly_deg": 0.0,
    "period_seconds": 5062.2,
    "period_minutes": 84.4
}
```

### Maneuver Endpoints

#### Hohmann Transfer
**POST** `/api/maneuvers/hohmann`

Request:
```json
{
    "r1_km": 6778,
    "r2_km": 42164
}
```

Response:
```json
{
    "r1_km": 6778,
    "r2_km": 42164,
    "delta_v1_km_s": 2.427,
    "delta_v2_km_s": 1.636,
    "total_delta_v_km_s": 4.063,
    "transfer_time_seconds": 21651.6,
    "transfer_time_hours": 6.01,
    "transfer_semi_major_axis_km": 24471
}
```

---

## 🧮 Modules & Components

### Core Orbital Mechanics Library

#### `constants.py`
Physical and orbital constants:
- Earth parameters (radius, gravitational parameter)
- J2, J3, J4 zonal harmonics
- Common orbital elements for various orbit types
- Conversions and time scales

#### `conversions.py`
Bidirectional orbital element conversions:
- Cartesian state vectors ↔ Keplerian elements
- Mean anomaly ↔ True anomaly (Kepler's equation)
- Orbital period, velocity, energy, angular momentum calculations

**Key Functions:**
- `cartesian_to_keplerian()` - State vectors to orbital elements
- `keplerian_to_cartesian()` - Orbital elements to state vectors
- `mean_anomaly_to_true_anomaly()` - Solve Kepler's equation
- `orbital_period()` - Calculate orbital period
- `orbital_velocity()` - Calculate velocity at given radius

#### `tle.py`
Two-Line Element Set handling:
- **TLE Class**: Parse, store, and access TLE data
- NORAD format parsing (line 1 & 2)
- Epoch datetime calculation
- CelesTrak integration (fetch live TLE data)

**Key Functions:**
- `parse_tle()` - Parse TLE from strings
- `parse_tle_string()` - Parse multi-line TLE format
- `tle_from_celestrak_url()` - Fetch from CelesTrak
- `semi_major_axis_from_mean_motion()` - Calculate semi-major axis

#### `propagators.py`
Orbital propagation engines:

**TwoBodyPropagator**: Classical Keplerian propagation
- Assumes spherical central body
- No perturbations
- Educational use, quick estimation
- RK4/5 numerical integration

**J2Propagator**: Linearized J2 oblateness perturbation
- Includes RAAN precession (nodal regression)
- Includes apsidal advance (argument of perigee)
- Medium-term accuracy (days to weeks)
- Time-averaged perturbation rates

**SGP4Wrapper**: NORAD standard propagator
- Wraps sgp4 library
- TLE-based propagation
- Industry standard for LEO/GEO
- Accurate short-term predictions

**Key Functions:**
- `propagate()` - Integrate orbit forward in time
- `compare_propagators()` - Compare multiple methods
- `get_raan_precession_rate_deg_per_day()` - J2 effects analysis

#### `maneuvers.py`
Orbital maneuver calculators:

**HohmannTransfer**: Two-impulse transfer between circular coplanar orbits
- Minimum energy transfer
- Calculates ΔV₁, ΔV₂, total ΔV
- Transfer time calculation

**BiellipticTransfer**: Three-impulse transfer
- More efficient for large radius ratios (r₂/r₁ > 11.94)
- Optional intermediate radii
- Good for high-energy missions

**PlaneChange**: Inclination change maneuver
- Simple plane change (perpendicular impulse)
- Hohmann-combined plane change
- More efficient at apoapsis

**OrbitalManeuverSequence**: Chain multiple maneuvers
- Combined ΔV tracking
- Total mission planning

#### `ground_track.py`
Ground track and access calculations:

**GroundTrack**: Sub-satellite point tracking
- Computes latitude/longitude over time
- Accounts for Earth rotation
- Altitude calculation

**AccessCalculator**: Visibility analysis from ground stations
- Line-of-sight calculations
- Elevation angle masking
- Access windows (AOS/LOS detection)
- Slant range and azimuth

**Utility Functions:**
- `compute_horizon_distance()` - Ground coverage calculations
- `compute_sun_angle()` - Eclipse calculations

#### `orbit_catalog.py`
Comprehensive orbital type database with 11 orbit types:

| Orbit Type | Altitude | Eccentricity | Inclination | Uses |
|------------|----------|-------|-------------|------|
| LEO | 200-2000 km | 0.0-0.1 | Variable | Earth obs, ISS |
| SSO | 600-1000 km | 0.0-0.1 | ~98° | Land imaging |
| GEO | 35,786 km | ~0 | ~0° | Weather, comms |
| Molniya | 500-39,600 | 0.74 | 63.4° | High-lat comms |
| Polar | 400-1000 km | 0.0-0.1 | ~90° | Polar coverage |
| Tundra | 5000-46000 | 0.6 | 63.4° | Arctic comms |
| Semisynchronous | 20,184 km | 0.002 | 55° | GPS |
| Lunar | 100-400 km | 0.0-0.1 | Variable | Lunar missions |
| Heliocentric | AU scale | Variable | Variable | Solar/Mars |

Each orbit includes:
- Real spacecraft examples
- Launch characteristics
- Performance metrics
- Use cases and advantages/disadvantages

---

## 📚 References & Citations

### Primary References

1. **Curtis, H. D. (2013).** *Orbital Mechanics for Engineering Students* (3rd ed.). Butterworth-Heinemann. ISBN 978-0-08-102133-0.
   - Fundamental reference for all orbital mechanics calculations
   - Algorithms 4.1-4.2 (state vector conversions)
   - Sections 7.3-7.5 (maneuvers and transfers)

2. **Vallado, D. A., Crawford, P., Hujsak, R., & Kelso, T. S. (2006).** "Revisiting Spacetrack Report #3: Rev 1." AIAA Paper 2006-6753.
   - NORAD TLE propagation standards
   - SGP4/SDP4 propagator specification
   - J2 perturbation analysis

3. **NORAD Two-Line Element Set Format.** https://celestrak.org/NORAD/documentation/tle-fmt.php
   - Official TLE format specification
   - Historical context and standardization

### Additional References

- **SGP4 Library:** https://pypi.org/project/sgp4/
- **CesiumJS Documentation:** https://cesium.com/platform/cesiumjs/
- **NASA Orbital Mechanics Resources:** https://www.nasa.gov/
- **CelesTrak Satellite Database:** https://celestrak.org/

---

## 🛠️ Development

### Running Tests

```bash
cd backend
python -m pytest tests/  # If tests exist
```

### Code Structure

```
backend/orbital_mechanics/
├── constants.py          # No dependencies - pure data
├── conversions.py        # Depends: constants, numpy, scipy
├── tle.py              # Depends: constants, conversions, requests
├── propagators.py      # Depends: constants, conversions, scipy
├── maneuvers.py        # Depends: constants, conversions
├── ground_track.py     # Depends: constants, conversions
└── orbit_catalog.py    # Depends: constants
```

### Adding New Propagators

Extend `propagators.py` with new `Propagator` classes following this interface:

```python
class MyPropagator:
    def __init__(self, initial_state):
        """Initialize with initial orbital state"""
        pass
    
    def propagate(self, dt):
        """Propagate dt seconds forward, return new state"""
        pass
    
    def get_summary(self):
        """Return summary dict of propagator characteristics"""
        pass
```

---

## 🎓 Educational Value

### For Students
- **Foundation**: Understand orbital mechanics principles hands-on
- **STK Preparation**: CesiumJS visualization mirrors STK concepts
- **Career Prep**: Flight operations engineer preparation material

### For Educators
- Open-source educational resource
- Modular code structure for teaching
- Real data integration (live TLE)

### For Flight Operations
- Quick ΔV estimation tools
- Maneuver planning reference
- Propagator comparison for mission analysis


