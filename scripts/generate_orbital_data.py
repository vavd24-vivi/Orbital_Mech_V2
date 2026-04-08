#!/usr/bin/env python3
"""
Orbital Data Pre-computation Script
====================================
Generates / refreshes all static JSON data files served from /public/data/.

Usage
-----
    python scripts/generate_orbital_data.py            # update timestamp only
    python scripts/generate_orbital_data.py --fetch-live  # also pull fresh TLEs

Outputs (in /public/data/)
--------------------------
  tle-database.json         — real TLE snapshots with source metadata
  missions.json             — historical mission parameters (static; manual update)
  orbit-types.json          — orbit classification catalog (static; manual update)
  precomputed-groundtracks.json  — pre-propagated ground tracks (recomputed here)
  perturbation-analysis.json     — J2–J4 perturbation rates (recomputed here)

and updates the DATA_UPDATED constant in /public/data-config.js.

References
----------
    Vallado, D. A. (2013). Fundamentals of Astrodynamics and Applications
        (4th ed.). Microcosm Press & Springer.
    Curtis, H. D. (2013). Orbital Mechanics for Engineering Students (3rd ed.).
        Butterworth-Heinemann. ISBN 978-0-08-102133-0.
    CelesTrak TLE sources: https://celestrak.org/NORAD/elements/
"""

import argparse
import json
import math
import os
import re
import sys
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = os.path.join(REPO_ROOT, "public", "data")
CONFIG_FILE = os.path.join(REPO_ROOT, "public", "data-config.js")

# ---------------------------------------------------------------------------
# Earth constants
# ---------------------------------------------------------------------------
MU = 398600.4418        # km³/s²
RE = 6371.0             # km
J2 = 1.08263e-3
J3 = -2.53215e-6
J4 = -1.61991e-6
TWO_PI = 2 * math.pi


# ===========================================================================
# Orbital mechanics helpers
# ===========================================================================

def mean_motion_to_sma(n_rpm: float) -> float:
    """Mean motion (rev/day) → semi-major axis (km)."""
    n = n_rpm * TWO_PI / 86400          # rad/s
    return (MU / n**2) ** (1 / 3)


def orbital_velocity(r: float, a: float) -> float:
    """Vis-viva velocity at radius r on orbit with SMA a (km/s)."""
    return math.sqrt(MU * (2 / r - 1 / a))


def orbital_period(a: float) -> float:
    """Orbital period in seconds."""
    return TWO_PI * math.sqrt(a**3 / MU)


def j2_rates(a: float, e: float, i_deg: float):
    """
    Return secular J2 RAAN and AoP precession rates in rad/s.

    Parameters
    ----------
    a : float — semi-major axis (km)
    e : float — eccentricity
    i_deg : float — inclination (degrees)

    Returns
    -------
    raan_dot_rad_s, aop_dot_rad_s
    """
    i = math.radians(i_deg)
    p = a * (1 - e**2)
    n = math.sqrt(MU / a**3)
    factor = -1.5 * n * J2 * (RE / p)**2
    raan_dot = factor * math.cos(i)
    aop_dot  = factor * (2.5 * math.sin(i)**2 - 2)
    return raan_dot, aop_dot


def j3_raan_rate(a: float, e: float, i_deg: float) -> float:
    """First-order J3 RAAN rate (rad/s)."""
    i = math.radians(i_deg)
    p = a * (1 - e**2)
    n = math.sqrt(MU / a**3)
    return -1.5 * n * J3 * (RE / p)**3 * math.cos(i) * (4 - 5 * math.sin(i)**2)


def j4_raan_rate(a: float, e: float, i_deg: float) -> float:
    """First-order J4 RAAN rate (rad/s)."""
    i = math.radians(i_deg)
    p = a * (1 - e**2)
    n = math.sqrt(MU / a**3)
    return 1.875 * n * J4 * (RE / p)**4 * math.cos(i) * (1 - 7 / 6 * math.sin(i)**2)


# ---------------------------------------------------------------------------
# Kepler equation solver
# ---------------------------------------------------------------------------

def kepler_newton(M: float, e: float, tol: float = 1e-10) -> float:
    """Solve M = E - e sin E for eccentric anomaly E (radians)."""
    E = M if e < 0.8 else math.pi
    for _ in range(50):
        dE = (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
        E -= dE
        if abs(dE) < tol:
            break
    return E


def mean_to_true(M: float, e: float) -> float:
    """Mean anomaly M → true anomaly ν (radians)."""
    E = kepler_newton(M % TWO_PI, e)
    return 2 * math.atan2(
        math.sqrt(1 + e) * math.sin(E / 2),
        math.sqrt(1 - e) * math.cos(E / 2)
    )


# ---------------------------------------------------------------------------
# Keplerian → ECI state vector
# ---------------------------------------------------------------------------

def keplerian_to_eci(a, e, i_deg, raan_deg, aop_deg, nu_deg):
    """
    Convert Keplerian elements to ECI state vector (pure Python, no numpy).
    Curtis (2013) Algorithm 4.2.

    Returns (r_eci [km], v_eci [km/s]) as plain lists
    """
    i  = math.radians(i_deg)
    ra = math.radians(raan_deg)
    w  = math.radians(aop_deg)
    nu = math.radians(nu_deg)

    p = a * (1 - e**2)
    r = p / (1 + e * math.cos(nu))

    # Perifocal frame
    r_pf = [r * math.cos(nu), r * math.sin(nu), 0.0]
    sqMup = math.sqrt(MU / p)
    v_pf = [-sqMup * math.sin(nu), sqMup * (e + math.cos(nu)), 0.0]

    # Rotation matrix: perifocal → ECI
    cw, sw = math.cos(w), math.sin(w)
    ci, si = math.cos(i), math.sin(i)
    co, so = math.cos(ra), math.sin(ra)

    Q = [
        [co*cw - so*sw*ci,  -co*sw - so*cw*ci,  so*si],
        [so*cw + co*sw*ci,  -so*sw + co*cw*ci, -co*si],
        [sw*si,              cw*si,              ci   ]
    ]

    # Matrix × vector
    def mv(M, v):
        return [M[r][0]*v[0] + M[r][1]*v[1] + M[r][2]*v[2] for r in range(3)]

    return mv(Q, r_pf), mv(Q, v_pf)


# ---------------------------------------------------------------------------
# ECI → Geodetic
# ---------------------------------------------------------------------------

def eci_to_geodetic(r_eci, t_from_j2000_s: float):
    """
    Simplified ECI to geodetic (spherical Earth).

    Parameters
    ----------
    r_eci : array-like [x,y,z] km
    t_from_j2000_s : float — seconds since J2000 epoch

    Returns
    -------
    lat_deg, lon_deg, alt_km
    """
    OMEGA_E = 7.2921150e-5  # rad/s
    GMST0   = math.radians(280.46061837)

    x, y, z = r_eci
    r_mag = math.sqrt(x**2 + y**2 + z**2)
    lat   = math.degrees(math.asin(max(-1.0, min(1.0, z / r_mag))))

    gmst   = GMST0 + OMEGA_E * t_from_j2000_s
    lon_eci = math.atan2(y, x)
    lon = math.degrees(lon_eci - gmst) % 360
    if lon > 180:
        lon -= 360

    return lat, lon, r_mag - RE


# ===========================================================================
# Ground track computation
# ===========================================================================

def compute_ground_track(elements: dict, t0_j2000_s: float,
                         num_orbits: float = 2.0, step_s: int = 60):
    """
    Generate a ground track from Keplerian elements.

    Returns list of dicts: [{t_min, lat, lon, alt}, ...]
    """
    a     = elements["semi_major_axis_km"]
    e     = elements["eccentricity"]
    i_deg = elements["inclination_deg"]
    raan  = elements["raan_deg"]
    aop   = elements["arg_perigee_deg"]
    nu0   = elements["true_anomaly_deg"]

    T = orbital_period(a)                     # seconds
    total_t = num_orbits * T
    n_steps = max(2, int(total_t / step_s))

    # Compute J2 secular rates
    raan_dot, aop_dot = j2_rates(a, e, i_deg)  # rad/s

    # Initial eccentric → mean anomaly
    nu_r = math.radians(nu0)
    E0 = 2 * math.atan2(math.sqrt(1 - e) * math.sin(nu_r / 2),
                        math.sqrt(1 + e) * math.cos(nu_r / 2))
    M0 = E0 - e * math.sin(E0)
    n_rad = math.sqrt(MU / a**3)              # rad/s

    points = []
    for k in range(n_steps):
        dt = k * step_s
        M = (M0 + n_rad * dt) % TWO_PI
        nu = math.degrees(mean_to_true(M, e))

        # Apply J2 secular drift
        raan_t = raan + math.degrees(raan_dot * dt)
        aop_t  = aop  + math.degrees(aop_dot  * dt)

        r_eci, _ = keplerian_to_eci(a, e, i_deg, raan_t, aop_t, nu)
        lat, lon, alt = eci_to_geodetic(r_eci, t0_j2000_s + dt)

        points.append({
            "t_min": round(dt / 60, 2),
            "lat":   round(lat, 3),
            "lon":   round(lon, 3),
            "alt":   round(alt, 1)
        })

    return points


# ===========================================================================
# Perturbation analysis
# ===========================================================================

def compute_perturbation_rates(a, e, i_deg):
    """Return perturbation rate summary dict (rates in deg/day)."""
    raan_dot, aop_dot = j2_rates(a, e, i_deg)
    raan_j3 = j3_raan_rate(a, e, i_deg)
    raan_j4 = j4_raan_rate(a, e, i_deg)

    conv = math.degrees(1) * 86400   # rad/s → deg/day

    return {
        "j2_raan_rate_deg_per_day":      round(raan_dot * conv, 5),
        "j2_aop_rate_deg_per_day":       round(aop_dot  * conv, 5),
        "j3_raan_correction_deg_per_day":round(raan_j3  * conv, 7),
        "j4_raan_correction_deg_per_day":round(raan_j4  * conv, 7),
        "total_raan_rate_deg_per_day":   round((raan_dot + raan_j3 + raan_j4) * conv, 5),
        "raan_precession_deg_per_year":  round((raan_dot + raan_j3 + raan_j4) * conv * 365.25, 2),
    }


# ===========================================================================
# TLE fetching (optional; only with --fetch-live flag)
# ===========================================================================

CELESTRAK_TLE_URLS = {
    "stations":  "https://celestrak.org/NORAD/elements/stations.txt",
    "starlink":  "https://celestrak.org/NORAD/elements/starlink.txt",
    "gps_ops":   "https://celestrak.org/NORAD/elements/gps-ops.txt",
    "weather":   "https://celestrak.org/NORAD/elements/weather.txt",
    "science":   "https://celestrak.org/NORAD/elements/science.txt",
}

# NORAD IDs we want to keep in the database
TARGET_NORAD_IDS = {
    25544: "ISS (ZARYA)",
    20580: "HUBBLE SPACE TELESCOPE",
    50463: "JWST",
    44713: "STARLINK-1007",
    55768: "STARLINK-5678",
    24876: "GPS BIIR-2  (PRN 13)",
    40105: "GPS BIIF-10 (PRN 08)",
    51850: "GOES 18",
    41866: "GOES 16",
    40697: "SENTINEL-2A",
    49260: "LANDSAT 9",
    43013: "NOAA 20",
    25994: "TERRA",
}


def fetch_tle_from_celestrak(url: str) -> list:
    """
    Fetch three-line TLE sets from a CelesTrak URL.

    Returns list of dicts: [{name, line1, line2}, ...]
    """
    import urllib.request
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            text = resp.read().decode("utf-8")
    except Exception as exc:
        print(f"  Warning: could not fetch {url}: {exc}", file=sys.stderr)
        return []

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    tles = []
    i = 0
    while i + 2 < len(lines):
        if lines[i + 1].startswith("1 ") and lines[i + 2].startswith("2 "):
            tles.append({"name": lines[i], "line1": lines[i + 1], "line2": lines[i + 2]})
            i += 3
        else:
            i += 1
    return tles


def refresh_tle_database(existing_db: dict, retrieval_date: str) -> dict:
    """
    Fetch fresh TLEs for known satellites from CelesTrak and merge into
    the existing database, updating only entries that are found.
    """
    fresh_map = {}   # norad_id → {name, line1, line2}

    for source, url in CELESTRAK_TLE_URLS.items():
        print(f"  Fetching TLEs from {url} …")
        tles = fetch_tle_from_celestrak(url)
        for t in tles:
            try:
                norad = int(t["line2"][2:7])
                if norad in TARGET_NORAD_IDS:
                    fresh_map[norad] = t
            except (ValueError, IndexError):
                pass

    updated = 0
    for sat in existing_db.get("satellites", []):
        norad = sat.get("norad_id")
        if norad and norad in fresh_map:
            fresh = fresh_map[norad]
            sat["tle_line1"] = fresh["line1"]
            sat["tle_line2"] = fresh["line2"]
            sat["retrieval_date"] = retrieval_date
            # Parse new epoch
            try:
                yr2  = int(fresh["line1"][18:20])
                doy  = float(fresh["line1"][20:32])
                year = 1900 + yr2 if yr2 >= 57 else 2000 + yr2
                sat["epoch"] = f"{year}-{_doy_to_mmdd(year, doy)}"
            except Exception:
                pass
            updated += 1
            print(f"    Updated TLE for {sat['name']} (NORAD {norad})")

    print(f"  Updated {updated} of {len(existing_db.get('satellites', []))} TLE records.")
    return existing_db


def _doy_to_mmdd(year: int, doy: float) -> str:
    """Convert fractional day-of-year to MM-DD string."""
    from datetime import date, timedelta
    d = date(year, 1, 1) + timedelta(days=int(doy) - 1)
    return d.strftime("%m-%d")


# ===========================================================================
# Main
# ===========================================================================

def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Saved {os.path.relpath(path, REPO_ROOT)}")


def update_data_config_timestamp(iso_ts: str) -> None:
    """Replace DATA_UPDATED constant in data-config.js."""
    with open(CONFIG_FILE, encoding="utf-8") as f:
        src = f.read()

    new_src = re.sub(
        r"const DATA_UPDATED = '[^']+';",
        f"const DATA_UPDATED = '{iso_ts}';",
        src
    )
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(new_src)
    print(f"  Updated DATA_UPDATED timestamp in data-config.js → {iso_ts}")


def main():
    parser = argparse.ArgumentParser(description="Pre-compute orbital data files.")
    parser.add_argument("--fetch-live", action="store_true",
                        help="Fetch fresh TLEs from CelesTrak (requires internet)")
    args = parser.parse_args()

    now_utc   = datetime.now(timezone.utc)
    iso_now   = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    date_str  = now_utc.strftime("%Y-%m-%d")

    # J2000 reference
    j2000_unix = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc).timestamp()
    t0_j2000   = now_utc.timestamp() - j2000_unix

    print(f"\n{'='*60}")
    print(f"  Orbital Data Generator — {iso_now}")
    print(f"{'='*60}\n")

    os.makedirs(DATA_DIR, exist_ok=True)

    # ── 1. TLE database ──────────────────────────────────────────────────────
    print("[1/4] TLE database …")
    tle_path = os.path.join(DATA_DIR, "tle-database.json")
    tle_db   = load_json(tle_path)
    tle_db["_metadata"]["retrieval_date"] = date_str

    if args.fetch_live:
        print("  Fetching live TLEs from CelesTrak …")
        tle_db = refresh_tle_database(tle_db, date_str)
    else:
        print("  Skipping live fetch (use --fetch-live to update TLEs).")

    save_json(tle_path, tle_db)

    # ── 2. Pre-computed ground tracks ────────────────────────────────────────
    print("\n[2/4] Pre-computing ground tracks …")
    gt_path = os.path.join(DATA_DIR, "precomputed-groundtracks.json")
    gt_db   = load_json(gt_path)
    gt_db["_metadata"]["reference_epoch"] = iso_now

    for gt in gt_db.get("ground_tracks", []):
        name = gt.get("satellite", "?")
        els  = gt.get("orbital_elements_at_epoch", {})
        if not els:
            continue

        print(f"  Computing ground track for {name} …")
        try:
            points = compute_ground_track(
                els, t0_j2000,
                num_orbits=2.0,
                step_s=60
            )
            gt["track_points"]    = points
            gt["num_points"]      = len(points)
            gt["epoch"]           = iso_now
            gt["duration_minutes"]= round(len(points))
        except Exception as exc:
            print(f"    Warning: {exc}", file=sys.stderr)

    save_json(gt_path, gt_db)

    # ── 3. Perturbation analysis ─────────────────────────────────────────────
    print("\n[3/4] Recomputing perturbation rates …")
    pert_path = os.path.join(DATA_DIR, "perturbation-analysis.json")
    pert_db   = load_json(pert_path)
    pert_db["_metadata"]["reference_epoch"] = iso_now

    for scenario in pert_db.get("raan_precession_by_orbit", []):
        a     = scenario.get("semi_major_axis_km")
        e     = scenario.get("eccentricity", 0)
        i_deg = scenario.get("inclination_deg")
        if a and i_deg is not None:
            rates = compute_perturbation_rates(a, e, i_deg)
            scenario["results"].update(rates)
            print(f"  Updated: {scenario['scenario']}")

    save_json(pert_path, pert_db)

    # ── 4. Update timestamp in JS config ─────────────────────────────────────
    print("\n[4/4] Updating data-config.js timestamp …")
    update_data_config_timestamp(iso_now)

    print(f"\n{'='*60}")
    print(f"  Done. All data files updated at {iso_now}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
