"""
Orbital mechanics constants and physical parameters.
Values sourced from NORAD, NASA, and CODATA standards.

References:
- Vallado, D. A., Crawford, P., Hujsak, R., & Kelso, T. S. (2006).
  Revisiting Spacetrack Report #3. AIAA Paper 2006-6753.
- NORAD Two-Line Element Set Format. https://celestrak.org/NORAD/documentation/tle-fmt.php
"""

import math

# Earth Parameters
EARTH_RADIUS_KM = 6371.0  # Mean Earth radius (km)
EARTH_RADIUS_EQUATORIAL_KM = 6378.137  # Equatorial radius WGS84 (km)
EARTH_RADIUS_POLAR_KM = 6356.752  # Polar radius WGS84 (km)

# Gravitational Parameters
GM_EARTH_KM3_S2 = 398600.4418  # Standard gravitational parameter for Earth (km³/s²)
GM_SUN_KM3_S2 = 132712440018.0  # Standard gravitational parameter for Sun (km³/s²)

# Earth Rotation
EARTH_ROTATION_RATE_RAD_S = 7.2921151467e-5  # Angular velocity (rad/s)
EARTH_ROTATION_RATE_DEG_DAY = 360.98564724  # Rotation in degrees per sidereal day
SIDEREAL_DAY_SECONDS = 86164.0905  # Seconds per sidereal day

# J2 Perturbation
J2 = 1.08262668355e-3  # Earth's oblateness coefficient (zonal harmonic J2)
J3 = -2.53241051e-6   # Earth's zonal harmonic J3
J4 = -1.61098761e-6   # Earth's zonal harmonic J4

# Atmospheric Model Parameters
SCALE_HEIGHT_KM = 8.5  # Atmospheric scale height (km)

# Time Scales
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400
SECONDS_PER_JULIAN_CENTURY = 36525 * 86400

# Conversions
DEG_TO_RAD = math.pi / 180.0
RAD_TO_DEG = 180.0 / math.pi

# Standard Orbital Parameters
SEMI_MAJOR_AXIS_LEO_KM = 6700.0  # Typical LEO altitude ~330 km
SEMI_MAJOR_AXIS_GEO_KM = 42164.0  # GEO semi-major axis
SEMI_MAJOR_AXIS_MOLNIYA_KM = 26600.0  # Molniya orbit semi-major axis
SEMI_MAJOR_AXIS_ISS_KM = 6738.0  # ISS orbit (altitude ~408 km)

# Common Inclinations (degrees)
INCLINATION_LEO_DEG = 51.6  # ISS and typical LEO inclination
INCLINATION_GEO_DEG = 0.0  # Geostationary equatorial
INCLINATION_MOLNIYA_DEG = 63.4  # Molniya highly elliptical
INCLINATION_POLAR_DEG = 90.0  # Polar orbit
INCLINATION_SSO_DEG = 98.0  # Sun Synchronous Orbit

# Orbital Elements for Common Orbits (for reference)
ORBIT_TYPES = {
    "LEO": {
        "altitude_km": 400,
        "description": "Low Earth Orbit",
        "eccentricity": 0.0,
        "inclination_deg": 51.6,
        "period_minutes": 92.9
    },
    "GEO": {
        "altitude_km": 35786,
        "description": "Geostationary Orbit",
        "eccentricity": 0.0001,
        "inclination_deg": 0.0,
        "period_minutes": 1440.0
    },
    "SSO": {
        "altitude_km": 800,
        "description": "Sun Synchronous Orbit",
        "eccentricity": 0.0,
        "inclination_deg": 98.0,
        "period_minutes": 102.0
    },
    "MOLNIYA": {
        "altitude_km": 39600,
        "description": "Highly Elliptical (Molniya)",
        "eccentricity": 0.74,
        "inclination_deg": 63.4,
        "period_minutes": 720.0
    }
}

# Reference Epochs
EPOCH_J2000_JD = 2451545.0  # Julian Date for J2000 epoch (2000 January 1, 12:00 TT)
EPOCH_J2000_MJD = 51544.5  # Modified Julian Date for J2000

# Speed of Light
SPEED_OF_LIGHT_KM_S = 299792.458
