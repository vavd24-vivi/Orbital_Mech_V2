/**
 * Data Configuration — replaces firebase-config.js
 *
 * All computations now run client-side via orbital-calculations.js.
 * JSON datasets are served as static files from /data/.
 * No Firebase SDK, no Cloud Functions, no paid-tier requirements.
 *
 * Data sources:
 *   CelesTrak (https://celestrak.org) — NORAD TLE data (public domain)
 *   NASA NSSDCA (https://nssdc.gsfc.nasa.gov) — mission parameters
 *   NASA JPL Horizons — ephemeris data for Lagrange-point missions
 */

'use strict';

// ─── Data-last-updated timestamp ────────────────────────────────────────────
// Updated automatically by .github/workflows/update-data.yml weekly.
const DATA_UPDATED = '2026-04-08T13:07:16Z';

// ─── Base paths ──────────────────────────────────────────────────────────────
const DATA_BASE = 'data';

// ─── Simple in-memory cache ──────────────────────────────────────────────────
const _cache = {};

/**
 * Fetch a JSON data file with caching.
 * Falls back gracefully to an empty object if the file is unavailable.
 *
 * @param {string} filename - File inside /data/ (e.g. 'tle-database.json')
 * @returns {Promise<any>}
 */
async function loadDataFile(filename) {
    if (_cache[filename]) return _cache[filename];
    try {
        const resp = await fetch(`${DATA_BASE}/${filename}`);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        _cache[filename] = data;
        return data;
    } catch (err) {
        console.warn(`[data-config] Could not load ${filename}:`, err.message);
        return {};
    }
}

// ─── apiCall shim — replaces the old Firebase / Cloud-Functions apiCall() ───
//
// Endpoints handled:
//   GET  /orbits/list
//   POST /orbits/info
//   POST /tle/parse
//   POST /conversions/keplerian-to-state
//   POST /maneuvers/hohmann
//   POST /animation/orbit-frames
//   POST /animation/ground-track-trace
//   POST /animation/comparative
//   POST /mission-planning/launch-windows
//   POST /perturbations/advanced

/**
 * Drop-in replacement for the old apiCall(endpoint, method, data) function.
 * All computation now happens in the browser via OrbitalCalc.
 *
 * @param {string} endpoint - API path (e.g. '/tle/parse')
 * @param {string} [method='GET'] - HTTP verb (ignored; kept for compatibility)
 * @param {any}    [data=null]    - Request payload
 * @returns {Promise<any>}
 */
async function apiCall(endpoint, method = 'GET', data = null) {
    // Strip leading slash for switch matching
    const path = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;

    switch (path) {

        // ── Orbit catalogue ─────────────────────────────────────────────────
        case 'orbits/list': {
            const catalog = OrbitalCalc.getOrbitCatalog();
            return { orbits: catalog.map(o => o.id) };
        }

        case 'orbits/info': {
            const catalog = OrbitalCalc.getOrbitCatalog();
            const orbit   = catalog.find(o => o.id === data?.orbit_type) || catalog[0];
            return orbit;
        }

        // ── TLE parsing ─────────────────────────────────────────────────────
        case 'tle/parse': {
            const { name = 'UNKNOWN', line1, line2 } = data || {};
            try {
                return OrbitalCalc.parseTLE(name, line1, line2);
            } catch (e) {
                return { error: e.message };
            }
        }

        // ── Keplerian → state vectors ───────────────────────────────────────
        case 'conversions/keplerian-to-state': {
            const {
                semi_major_axis_km: a   = 6778,
                eccentricity: e         = 0,
                inclination_deg: i      = 0,
                raan_deg: raan          = 0,
                argument_of_perigee_deg: aop = 0,
                true_anomaly_deg: nu    = 0
            } = data || {};
            const sv = OrbitalCalc.keplerianToCartesian(a, e, i, raan, aop, nu);
            return { position: sv.position, velocity: sv.velocity };
        }

        // ── Hohmann transfer ─────────────────────────────────────────────────
        case 'maneuvers/hohmann': {
            const { r1_km = 6778, r2_km = 42164 } = data || {};
            try {
                return OrbitalCalc.hohmannTransfer(r1_km, r2_km);
            } catch (e) {
                return { error: e.message };
            }
        }

        // ── Animation frames ─────────────────────────────────────────────────
        case 'animation/orbit-frames': {
            return OrbitalCalc.generateOrbitFrames(data || {});
        }

        // ── Ground-track trace ───────────────────────────────────────────────
        case 'animation/ground-track-trace': {
            // Accept either raw keplerian params or a satellite_tle field
            let params = Object.assign({}, data || {});
            if (params.satellite_tle) {
                try {
                    const tleLines = params.satellite_tle.trim().split('\n');
                    if (tleLines.length >= 2) {
                        const name  = tleLines.length === 3 ? tleLines[0] : 'SAT';
                        const l1    = tleLines[tleLines.length - 2];
                        const l2    = tleLines[tleLines.length - 1];
                        const tle   = OrbitalCalc.parseTLE(name, l1, l2);
                        params = Object.assign(params, {
                            semi_major_axis_km:  tle.semi_major_axis_km,
                            eccentricity:        tle.eccentricity,
                            inclination_deg:     tle.inclination_deg,
                            raan_deg:            tle.raan_deg,
                            arg_perigee_deg:     tle.argument_of_perigee_deg,
                            true_anomaly_deg:    tle.mean_anomaly_deg   // approximate
                        });
                    }
                } catch (_) { /* fall through with raw params */ }
            }
            params.num_orbits       = params.num_orbits       ?? 3;
            params.steps_per_orbit  = params.steps_per_orbit  ?? 180;
            return OrbitalCalc.generateGroundTrack(params);
        }

        // ── Comparative propagation ──────────────────────────────────────────
        case 'animation/comparative': {
            const { position, velocity, num_orbits = 1 } = data || {};
            if (!position || !velocity) {
                return { error: 'position and velocity required', frames: [] };
            }
            const kep = OrbitalCalc.cartesianToKeplerian(position, velocity);
            const base = OrbitalCalc.generateOrbitFrames({
                semi_major_axis_km:  kep.semi_major_axis_km,
                eccentricity:        kep.eccentricity,
                inclination_deg:     kep.inclination_deg,
                raan_deg:            kep.raan_deg,
                arg_perigee_deg:     kep.arg_perigee_deg,
                true_anomaly_deg:    kep.true_anomaly_deg,
                num_orbits,
                steps_per_orbit: 360
            });
            // Two-body without J2 for comparison
            const noJ2Frames = OrbitalCalc.generateOrbitFrames({
                semi_major_axis_km:  kep.semi_major_axis_km,
                eccentricity:        kep.eccentricity,
                inclination_deg:     kep.inclination_deg,
                raan_deg:            kep.raan_deg,
                arg_perigee_deg:     kep.arg_perigee_deg,
                true_anomaly_deg:    kep.true_anomaly_deg,
                num_orbits,
                steps_per_orbit: 360,
                _skipJ2: true
            });

            const frames = base.frames.map((f, idx) => {
                const f2 = noJ2Frames.frames[idx] || f;
                const dr = [
                    f.position_eci[0] - f2.position_eci[0],
                    f.position_eci[1] - f2.position_eci[1],
                    f.position_eci[2] - f2.position_eci[2]
                ];
                const divergence = Math.sqrt(dr[0]*dr[0] + dr[1]*dr[1] + dr[2]*dr[2]);
                return Object.assign({}, f, {
                    position_divergence_km: divergence,
                    raan_difference_deg: 0    // placeholder for display
                });
            });
            return { frames };
        }

        // ── Launch windows ───────────────────────────────────────────────────
        case 'mission-planning/launch-windows': {
            return OrbitalCalc.computeLaunchWindows(data || {});
        }

        // ── Advanced perturbations ───────────────────────────────────────────
        case 'perturbations/advanced': {
            return OrbitalCalc.advancedPerturbationAnalysis(data || {});
        }

        default:
            console.warn('[data-config] Unknown endpoint:', endpoint);
            return { error: `Unknown endpoint: ${endpoint}` };
    }
}

// ─── Expose globals expected by existing JS files ───────────────────────────
// (firebase-config.js used to set API_BASE_URL and apiCall globally)
window.apiCall       = apiCall;
window.loadDataFile  = loadDataFile;
window.DATA_UPDATED  = DATA_UPDATED;
window.__firebaseReady = false;   // auth features disabled

// ─── Show data timestamp in UI when DOM is ready ────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    const el = document.getElementById('data-updated-badge');
    if (el) {
        const d = new Date(DATA_UPDATED);
        el.textContent = `Data: ${d.toLocaleDateString('en-US', { year:'numeric', month:'short', day:'numeric', timeZone:'UTC' })} UTC`;
        el.title = 'Static dataset — regenerated weekly by GitHub Actions';
    }
});
