"""
Orbital Type Catalog

Comprehensive catalog of major orbital types with characteristics,
uses, real spacecraft examples, and launch parameters.

References:
- Curtis, H. D. (2013). "Orbital Mechanics for Engineering Students" (3rd ed.).
- Vallado, D. A., Crawford, P., Hujsak, R., & Kelso, T. S. (2006).
  "Revisiting Spacetrack Report #3: Rev 1". AIAA Paper 2006-6753.
- NASA/NORAD Satellite Database
"""

from .constants import EARTH_RADIUS_KM, GM_EARTH_KM3_S2
import math


ORBIT_CATALOG = {
    "LEO": {
        "name": "Low Earth Orbit",
        "description": "Circular orbits with altitude 200-2000 km, typically used for Earth observation, ISS, and research",
        "altitude_range_km": (200, 2000),
        "typical_altitude_km": 400,
        "eccentricity_range": (0.0, 0.1),
        "typical_eccentricity": 0.0005,
        "inclination_range_deg": (0, 90),
        "typical_inclination_deg": 51.6,
        "examples": [
            {
                "name": "ISS (International Space Station)",
                "country": "International",
                "altitude_km": 408,
                "inclination_deg": 51.6,
                "period_minutes": 92.9,
                "use": "Research, Earth observation"
            },
            {
                "name": "Hubble Space Telescope",
                "country": "USA",
                "altitude_km": 545,
                "inclination_deg": 28.5,
                "period_minutes": 96.4,
                "use": "Space telescope"
            },
            {
                "name": "Aqua (NASA Earth science)",
                "country": "USA",
                "altitude_km": 705,
                "inclination_deg": 98.2,
                "period_minutes": 98.9,
                "use": "Earth observation"
            }
        ],
        "launch_characteristics": {
            "typical_delta_v_km_s": 9.3,
            "preferred_launch_sites": ["KSC (28.5°N)", "Baikonur (45.9°N)", "Vandenberg (34.4°N)"],
            "notes": "Inclination limited by launch site latitude. Lower inclinations easier from equatorial sites."
        },
        "uses": ["Earth observation", "Communications relay", "Scientific research", "Weather monitoring"],
        "advantages": ["Low launch costs", "Short orbital period", "High resolution Earth imagery"],
        "disadvantages": ["Limited satellite lifespan (5-15 years)", "Atmospheric drag", "Debris hazard"]
    },
    
    "SSO": {
        "name": "Sun-Synchronous Orbit",
        "description": "Special polar orbit where precession matches Earth's orbit around sun (~1° per day), maintains same local solar time",
        "altitude_range_km": (600, 1000),
        "typical_altitude_km": 800,
        "eccentricity_range": (0.0, 0.1),
        "typical_eccentricity": 0.001,
        "inclination_range_deg": (97, 99),
        "typical_inclination_deg": 98.2,
        "examples": [
            {
                "name": "Landsat 8",
                "country": "USA",
                "altitude_km": 705,
                "inclination_deg": 98.2,
                "period_minutes": 98.9,
                "use": "Land imaging"
            },
            {
                "name": "Sentinel-2",
                "country": "European Space Agency",
                "altitude_km": 786,
                "inclination_deg": 98.6,
                "period_minutes": 101.4,
                "use": "Multispectral imaging"
            }
        ],
        "launch_characteristics": {
            "typical_delta_v_km_s": 9.8,
            "preferred_launch_sites": ["Vandenberg (34.4°N)", "Plesetsk (62.9°N)"],
            "notes": "J2 perturbation used for nodal precession. Inclination ~98° maintains sun synchronicity."
        },
        "uses": ["Land mapping", "Coastal monitoring", "Agriculture", "Climate research"],
        "advantages": ["Consistent lighting conditions", "Constant local solar time", "Excellent for time-series analysis"],
        "disadvantages": ["High inclination", "Requires high latitude launch site", "Limited repeat swath coverage equator"]
    },
    
    "GEO": {
        "name": "Geostationary Orbit",
        "description": "Equatorial orbit at ~36,000 km altitude with 24-hour period, appears stationary over fixed point",
        "altitude_range_km": (35780, 35800),
        "typical_altitude_km": 35786,
        "eccentricity_range": (0.0001, 0.01),
        "typical_eccentricity": 0.0005,
        "inclination_range_deg": (-2, 2),
        "typical_inclination_deg": 0.0,
        "examples": [
            {
                "name": "GOES-16 (NOAA Weather)",
                "country": "USA",
                "altitude_km": 35786,
                "inclination_deg": 0.02,
                "period_minutes": 1440.0,
                "use": "Weather monitoring"
            },
            {
                "name": "Intelsat 39",
                "country": "USA",
                "altitude_km": 35786,
                "inclination_deg": 0.03,
                "period_minutes": 1440.0,
                "use": "Communications"
            }
        ],
        "launch_characteristics": {
            "typical_delta_v_km_s": 10.5,
            "preferred_launch_sites": ["Arianespace (French Guiana)", "Baikonur (45.9°N)"],
            "notes": "Achieved from LEO via GTO (Geostationary Transfer Orbit) or Hohmann transfer"
        },
        "uses": ["Weather monitoring", "Communications", "Broadcasting", "Earth observation (fixed region)"],
        "advantages": ["Stationary over point", "Continuous coverage", "Large footprint"],
        "disadvantages": ["Very high altitude", "Expensive", "High latency", "Limited high-latitude coverage"]
    },
    
    "MOLNIYA": {
        "name": "Highly Elliptical Orbit (Molniya)",
        "description": "Highly elliptical orbit (typically 63.4° inclination) with 12-hour period, covers high latitudes",
        "altitude_range_km": f"Perigee: 500-1000, Apogee: 39000-40000",
        "typical_altitude_km": "Varies: 500 (perigee) to 39600 (apogee)",
        "eccentricity_range": (0.6, 0.8),
        "typical_eccentricity": 0.74,
        "inclination_range_deg": (60, 65),
        "typical_inclination_deg": 63.4,
        "examples": [
            {
                "name": "Molniya 1-93 (Russia)",
                "country": "Russia",
                "altitude_km": "500/39600",
                "inclination_deg": 63.4,
                "period_minutes": 720.0,
                "use": "Communications over high latitudes"
            },
            {
                "name": "Blagoveshchensk (Russian communications)",
                "country": "Russia",
                "altitude_km": "500/39600",
                "inclination_deg": 63.4,
                "period_minutes": 720.0,
                "use": "Russia/Siberia coverage"
            }
        ],
        "launch_characteristics": {
            "typical_delta_v_km_s": 10.2,
            "preferred_launch_sites": ["Baikonur (45.9°N)"],
            "notes": "12-hour period means 2 satellites needed for continuous coverage. Excellent for polar communications."
        },
        "uses": ["High-latitude communications", "Siberian coverage", "Arctic surveillance", "Northern hemisphere broadcasting"],
        "advantages": ["Long dwell time at apogee", "High latitude coverage", "Multiple per day overhead"],
        "disadvantages": ["Complex ground station tracking", "High apogee altitude", "Eccentric orbit effects"]
    },
    
    "HEO": {
        "name": "Highly Elliptical Orbit (Generic)",
        "description": "Elliptical orbits with varying eccentricity and inclination, customized for mission needs",
        "altitude_range_km": "Varies widely",
        "typical_altitude_km": "Mission dependent",
        "eccentricity_range": (0.4, 0.95),
        "typical_eccentricity": 0.7,
        "inclination_range_deg": (0, 90),
        "typical_inclination_deg": "Mission dependent",
        "examples": [
            {
                "name": "ELSA-d (Astroscale debris collector)",
                "country": "Japan",
                "altitude_km": "500/1800",
                "inclination_deg": 97.5,
                "period_minutes": 105.0,
                "use": "Active debris removal"
            }
        ],
        "launch_characteristics": {
            "typical_delta_v_km_s": "Varies",
            "preferred_launch_sites": ["Various"],
            "notes": "Customized orbits for specific mission profiles"
        },
        "uses": ["Specialized missions", "Debris removal", "Constellation deployment"],
        "advantages": ["Flexible geometry", "Mission-optimized altitude profile"],
        "disadvantages": ["Complex tracking", "Requires mission-specific design"]
    },
    
    "POLAR": {
        "name": "Polar Orbit",
        "description": "Orbit with inclination ≈ 90°, passes over both poles, covers entire globe over time",
        "altitude_range_km": (400, 1000),
        "typical_altitude_km": 700,
        "eccentricity_range": (0.0, 0.1),
        "typical_eccentricity": 0.001,
        "inclination_range_deg": (88, 92),
        "typical_inclination_deg": 90.0,
        "examples": [
            {
                "name": "NOAA-18 (Weather satellite)",
                "country": "USA",
                "altitude_km": 863,
                "inclination_deg": 99.0,
                "period_minutes": 101.3,
                "use": "Polar weather monitoring"
            }
        ],
        "launch_characteristics": {
            "typical_delta_v_km_s": 9.5,
            "preferred_launch_sites": ["Vandenberg (34.4°N)", "Plesetsk (62.9°N)"],
            "notes": "Often combined with SSO for consistent lighting"
        },
        "uses": ["Polar weather", "Global coverage", "Polar ice monitoring"],
        "advantages": ["Global coverage", "Polar region focus", "High inclination"],
        "disadvantages": ["Difficult launch from equatorial sites", "Slow repeat coverage at equator"]
    },
    
    "EQUATORIAL": {
        "name": "Equatorial Orbit",
        "description": "Orbit with inclination ≈ 0°, remains above equator, used for GEO and equatorial communications",
        "altitude_range_km": (400, 35800),
        "typical_altitude_km": 1000,
        "eccentricity_range": (0.0, 0.1),
        "typical_eccentricity": 0.001,
        "inclination_range_deg": (-2, 2),
        "typical_inclination_deg": 0.0,
        "examples": [
            {
                "name": "Palapa (Indonesian communications)",
                "country": "Indonesia",
                "altitude_km": 35786,
                "inclination_deg": 0.5,
                "period_minutes": 1440.0,
                "use": "Regional communications"
            }
        ],
        "launch_characteristics": {
            "typical_delta_v_km_s": "Varies",
            "preferred_launch_sites": ["Ariane launch site (5.2°N)", "Baikonur (45.9°N)"],
            "notes": "Easiest to reach from equatorial launch sites"
        },
        "uses": ["Equatorial region coverage", "GEO", "Communications"],
        "advantages": ["Efficient from equatorial launch sites", "Equatorial coverage focus"],
        "disadvantages": ["Difficult to reach from high-latitude sites", "Limited polar coverage"]
    },
    
    "TUNDRA": {
        "name": "Tundra Orbit",
        "description": "24-hour eccentric orbit similar to GEO but with 63.4° inclination for continuous high-latitude coverage",
        "altitude_range_km": "Perigee: 5000, Apogee: 46000",
        "typical_altitude_km": "5000/46000",
        "eccentricity_range": (0.5, 0.7),
        "typical_eccentricity": 0.6,
        "inclination_range_deg": (60, 66),
        "typical_inclination_deg": 63.4,
        "examples": [
            {
                "name": "Sirius XM (Satellite Radio)",
                "country": "USA/Canada",
                "altitude_km": "5000/46000",
                "inclination_deg": 63.4,
                "period_minutes": 1440.0,
                "use": "High-latitude satellite radio"
            }
        ],
        "launch_characteristics": {
            "typical_delta_v_km_s": 10.5,
            "preferred_launch_sites": ["High-latitude sites preferred"],
            "notes": "Stationary relative to ground in high latitude region"
        },
        "uses": ["High-latitude communications", "Arctic coverage", "Siberian communications"],
        "advantages": ["Continuous high-latitude coverage", "24-hour period", "Avoids equator"],
        "disadvantages": ["Complex orbit", "High fuel requirements", "Expensive"]
    },
    
    "GEOCENTRIC": {
        "name": "Geocentric Transfer Orbit (GTO)",
        "description": "Intermediate elliptical orbit for transfers to GEO, uses Earth's rotation for efficiency",
        "altitude_range_km": "Perigee: 200, Apogee: 35786",
        "typical_altitude_km": "200/35786",
        "eccentricity_range": (0.7, 0.8),
        "typical_eccentricity": 0.77,
        "inclination_range_deg": (0, 28),
        "typical_inclination_deg": 28.5,
        "examples": [
            {
                "name": "Ariane 5 standard deployment",
                "country": "Europe",
                "altitude_km": "200/35786",
                "inclination_deg": 28.5,
                "period_minutes": 635.0,
                "use": "GEO satellite deployment"
            }
        ],
        "launch_characteristics": {
            "typical_delta_v_km_s": 1.5,
            "preferred_launch_sites": ["Ariane (5.2°N)", "Baikonur (45.9°N)"],
            "notes": "Not a final orbit - satellite uses own propellant for apogee raise to GEO"
        },
        "uses": ["GEO deployment", "Hohmann transfer staging"],
        "advantages": ["Efficient deployment", "Lower launch costs to GEO"],
        "disadvantages": ["Requires active orbit insertion", "Temporary orbit"]
    },
    
    "SEMISYNCHRONOUS": {
        "name": "Semisynchronous Orbit",
        "description": "12-hour orbit at ~26,560 km altitude, used for GPS constellation",
        "altitude_range_km": (20000, 21000),
        "typical_altitude_km": 20184,
        "eccentricity_range": (0.0, 0.02),
        "typical_eccentricity": 0.002,
        "inclination_range_deg": (50, 56),
        "typical_inclination_deg": 55.0,
        "examples": [
            {
                "name": "GPS IIF-12 (US Navigation)",
                "country": "USA",
                "altitude_km": 20184,
                "inclination_deg": 55.0,
                "period_minutes": 717.97,
                "use": "Global Positioning System"
            }
        ],
        "launch_characteristics": {
            "typical_delta_v_km_s": 10.0,
            "preferred_launch_sites": ["Cape Canaveral (28.5°N)"],
            "notes": "Part of GPS constellation - 24 satellites in 6 planes"
        },
        "uses": ["Satellite navigation", "GPS constellation", "Timing"],
        "advantages": ["Excellent for global positioning", "24-satellite constellation", "Precise timing"],
        "disadvantages": ["Still requires ground control", "Medium altitude"]
    },
    
    "LUNAR": {
        "name": "Lunar Orbit",
        "description": "Orbit around the Moon, used for lunar exploration and communication relay",
        "altitude_range_km": "100-400 km above lunar surface",
        "typical_altitude_km": 100,
        "eccentricity_range": (0.0, 0.1),
        "typical_eccentricity": 0.001,
        "inclination_range_deg": (0, 90),
        "typical_inclination_deg": 90.0,
        "examples": [
            {
                "name": "Lunar Reconnaissance Orbiter",
                "country": "USA",
                "altitude_km": 50,
                "inclination_deg": 90.0,
                "period_minutes": 112.0,
                "use": "Lunar mapping and relay"
            }
        ],
        "launch_characteristics": {
            "typical_delta_v_km_s": "11-15 (from Earth)",
            "preferred_launch_sites": ["Kennedy Space Center"],
            "notes": "Requires trans-lunar injection (TLI) from Earth"
        },
        "uses": ["Lunar exploration", "Communication relay", "Mapping", "Future moon base support"],
        "advantages": ["Unlike Earth orbits", "Lunar resources exploration", "Supporting moon missions"],
        "disadvantages": ["Long transfer time", "Expensive", "Lunar terrain effects"]
    },
    
    "HELIOCENTRIC": {
        "name": "Heliocentric (Sun-orbit)",
        "description": "Orbit around the Sun, used for solar observation and interplanetary missions",
        "altitude_range_km": "Varies (AU scale)",
        "typical_altitude_km": "1 AU ≈ 150 million km",
        "eccentricity_range": (0.0, 1.0),
        "typical_eccentricity": 0.5,
        "inclination_range_deg": (0, 90),
        "typical_inclination_deg": "Mission-dependent",
        "examples": [
            {
                "name": "Parker Solar Probe",
                "country": "USA",
                "altitude_km": "9.86 solar radii (perihelion)",
                "inclination_deg": 0.0,
                "period_minutes": "N/A (Heliocentric)",
                "use": "Solar wind study"
            }
        ],
        "launch_characteristics": {
            "typical_delta_v_km_s": "11.2+ from Earth",
            "preferred_launch_sites": ["Kennedy Space Center"],
            "notes": "Requires escape velocity from Earth, then solar orbit insertion"
        },
        "uses": ["Solar observation", "Interplanetary missions", "Deep space exploration"],
        "advantages": ["Infinite possibilities for deep space", "Scientific discovery"],
        "disadvantages": ["Very expensive", "Long flight times", "Communication delays"]
    }
}


def get_orbit_info(orbit_type):
    """
    Get orbital characteristics for a specific orbit type.
    
    Parameters
    ----------
    orbit_type : str
        Orbit type key (e.g., 'LEO', 'GEO', 'SSO')
    
    Returns
    -------
    dict
        Orbit information dictionary
    """
    if orbit_type not in ORBIT_CATALOG:
        raise ValueError(f"Unknown orbit type: {orbit_type}. Available: {list(ORBIT_CATALOG.keys())}")
    
    return ORBIT_CATALOG[orbit_type]


def list_all_orbits():
    """List all available orbit types."""
    return list(ORBIT_CATALOG.keys())


def calculate_orbital_period(altitude_km, mu=GM_EARTH_KM3_S2):
    """
    Calculate orbital period for circular orbit at given altitude.
    
    Parameters
    ----------
    altitude_km : float
        Altitude above Earth surface (km)
    mu : float
        Gravitational parameter (km³/s²)
    
    Returns
    -------
    float
        Orbital period (minutes)
    """
    a = EARTH_RADIUS_KM + altitude_km
    period_seconds = 2 * math.pi * math.sqrt(a**3 / mu)
    return period_seconds / 60.0
