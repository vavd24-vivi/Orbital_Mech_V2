/**
 * Orbital Calculations — Client-Side JavaScript Library
 *
 * Implements all orbital mechanics computations previously handled by
 * Firebase Cloud Functions (Python backend).  All math runs in the browser
 * so the site works 100 % offline after first load.
 *
 * References:
 *   Curtis, H. D. (2013). Orbital Mechanics for Engineering Students (3rd ed.).
 *     Butterworth-Heinemann. ISBN 978-0-08-102133-0.
 *   Vallado, D. A., Crawford, P., Hujsak, R., & Kelso, T. S. (2006).
 *     Revisiting Spacetrack Report #3: Rev 1. AIAA Paper 2006-6753.
 *   Bate, R. R., Mueller, D. D., & White, J. E. (1971). Fundamentals of
 *     Astrodynamics. Dover Publications. ISBN 978-0-486-60061-1.
 */

'use strict';

// ─── Constants ───────────────────────────────────────────────────────────────

const OC = {
    MU:             398600.4418,   // Earth GM  (km³/s²)
    RE:             6371.0,        // Earth mean radius (km)
    J2:             1.08263e-3,    // J2 zonal harmonic
    J3:             -2.53215e-6,   // J3 zonal harmonic
    J4:             -1.61991e-6,   // J4 zonal harmonic
    OMEGA_EARTH:    7.2921150e-5,  // Earth rotation rate (rad/s)
    DEG2RAD:        Math.PI / 180,
    RAD2DEG:        180 / Math.PI,
    TWO_PI:         2 * Math.PI,
    // Standard atmosphere scale height (km) — simplified exponential model
    SCALE_HEIGHT:   8.5,
    RHO0:           1.225e-9       // Sea-level density (kg/km³)
};


// ─── TLE Parsing ─────────────────────────────────────────────────────────────

/**
 * Parse a Two-Line Element set into an orbital elements object.
 *
 * @param {string} name - Satellite name (line 0)
 * @param {string} line1 - TLE line 1
 * @param {string} line2 - TLE line 2
 * @returns {Object} Parsed TLE data
 */
function parseTLE(name, line1, line2) {
    line1 = line1.trim();
    line2 = line2.trim();

    if (!line1.startsWith('1 ')) throw new Error("Line 1 must start with '1 '");
    if (!line2.startsWith('2 ')) throw new Error("Line 2 must start with '2 '");

    const catalogNumber = parseInt(line1.slice(2, 7));

    // Epoch
    const epochYear2 = parseInt(line1.slice(18, 20));
    const epochDay  = parseFloat(line1.slice(20, 32));
    const year = epochYear2 >= 57 ? 1900 + epochYear2 : 2000 + epochYear2;

    // BStar (atmospheric drag term)
    const bstarStr = line1.slice(53, 61).trim();
    let bstar = 0;
    if (bstarStr && bstarStr !== '00000-0' && bstarStr !== '00000+0') {
        const sign = bstarStr[0] === '-' ? -1 : 1;
        const raw  = bstarStr.replace(/^[+-]/, '');
        const mantissa = parseFloat(raw.slice(0, raw.length - 2)) / 1e5;
        const exp = parseInt(raw.slice(-2));
        bstar = sign * mantissa * Math.pow(10, exp);
    }

    // Line 2 elements
    const inclination       = parseFloat(line2.slice(8, 16));
    const raan              = parseFloat(line2.slice(17, 25));
    const eccentricity      = parseFloat('0.' + line2.slice(26, 33));
    const argOfPerigee      = parseFloat(line2.slice(34, 42));
    const meanAnomaly       = parseFloat(line2.slice(43, 51));
    const meanMotion        = parseFloat(line2.slice(52, 63));  // rev/day

    // Derived values
    const n  = meanMotion * OC.TWO_PI / 86400;                 // rad/s
    const a  = Math.pow(OC.MU / (n * n), 1 / 3);              // km
    const altitude = a - OC.RE;
    const period   = OC.TWO_PI * Math.sqrt(Math.pow(a, 3) / OC.MU) / 60; // minutes

    // Epoch datetime
    const epochDatetime = doyToDate(year, epochDay);

    return {
        satellite_name:          name.trim(),
        catalog_number:          catalogNumber,
        epoch_datetime:          epochDatetime.toISOString(),
        inclination_deg:         inclination,
        raan_deg:                raan,
        eccentricity:            eccentricity,
        argument_of_perigee_deg: argOfPerigee,
        mean_anomaly_deg:        meanAnomaly,
        mean_motion_rpm:         meanMotion,
        bstar:                   bstar,
        semi_major_axis_km:      a,
        altitude_km:             altitude,
        orbital_period_minutes:  period,
        line1,
        line2
    };
}

/** Convert year + fractional day-of-year to Date. */
function doyToDate(year, doy) {
    const base   = new Date(Date.UTC(year, 0, 1)); // Jan 1
    const msInDay = 86400000;
    return new Date(base.getTime() + (doy - 1) * msInDay);
}


// ─── Keplerian ↔ Cartesian Conversions ───────────────────────────────────────

/**
 * Convert Keplerian orbital elements to ECI Cartesian state vectors.
 * Curtis (2013) Algorithm 4.2
 *
 * @param {number} a  - Semi-major axis (km)
 * @param {number} e  - Eccentricity
 * @param {number} i  - Inclination (deg)
 * @param {number} raan - RAAN (deg)
 * @param {number} aop  - Argument of perigee (deg)
 * @param {number} nu   - True anomaly (deg)
 * @returns {{position: number[], velocity: number[]}}
 */
function keplerianToCartesian(a, e, i, raan, aop, nu) {
    const iR    = i    * OC.DEG2RAD;
    const raanR = raan * OC.DEG2RAD;
    const aopR  = aop  * OC.DEG2RAD;
    const nuR   = nu   * OC.DEG2RAD;

    const p = a * (1 - e * e);
    const r = p / (1 + e * Math.cos(nuR));

    // Perifocal frame
    const rPeri = [r * Math.cos(nuR), r * Math.sin(nuR), 0];
    const sqrtMup = Math.sqrt(OC.MU / p);
    const vPeri = [-sqrtMup * Math.sin(nuR), sqrtMup * (e + Math.cos(nuR)), 0];

    // Rotation matrix: Perifocal → ECI (R3(-raan) · R1(-i) · R3(-aop))
    const cosW  = Math.cos(aopR),  sinW  = Math.sin(aopR);
    const cosI  = Math.cos(iR),    sinI  = Math.sin(iR);
    const cosO  = Math.cos(raanR), sinO  = Math.sin(raanR);

    // Combined rotation columns
    const Q = [
        [cosO*cosW - sinO*sinW*cosI,  -cosO*sinW - sinO*cosW*cosI,  sinO*sinI],
        [sinO*cosW + cosO*sinW*cosI,  -sinO*sinW + cosO*cosW*cosI, -cosO*sinI],
        [sinW*sinI,                    cosW*sinI,                    cosI     ]
    ];

    const pos = matVec(Q, rPeri);
    const vel = matVec(Q, vPeri);

    return { position: pos, velocity: vel };
}

/** 3×3 matrix × 3-vector multiply. */
function matVec(M, v) {
    return [
        M[0][0]*v[0] + M[0][1]*v[1] + M[0][2]*v[2],
        M[1][0]*v[0] + M[1][1]*v[1] + M[1][2]*v[2],
        M[2][0]*v[0] + M[2][1]*v[1] + M[2][2]*v[2]
    ];
}

/**
 * Convert ECI Cartesian state vectors to Keplerian elements.
 * Curtis (2013) Algorithm 4.1
 *
 * @param {number[]} r - Position [x,y,z] km
 * @param {number[]} v - Velocity [vx,vy,vz] km/s
 * @returns {Object} Keplerian elements in degrees
 */
function cartesianToKeplerian(r, v) {
    const rMag = norm3(r);
    const vMag = norm3(v);

    const h    = cross3(r, v);
    const hMag = norm3(h);

    const xi = 0.5 * vMag * vMag - OC.MU / rMag;
    const a  = -OC.MU / (2 * xi);

    const eVec = [
        (vMag*vMag - OC.MU/rMag) * r[0] / OC.MU - dot3(r,v) * v[0] / OC.MU,
        (vMag*vMag - OC.MU/rMag) * r[1] / OC.MU - dot3(r,v) * v[1] / OC.MU,
        (vMag*vMag - OC.MU/rMag) * r[2] / OC.MU - dot3(r,v) * v[2] / OC.MU
    ];
    const e = norm3(eVec);

    const incl = Math.acos(Math.min(1, Math.max(-1, h[2] / hMag))) * OC.RAD2DEG;

    const nVec  = cross3([0, 0, 1], h);
    const nMag  = norm3(nVec);

    let raan = 0;
    if (nMag > 1e-10) {
        raan = Math.acos(Math.min(1, Math.max(-1, nVec[0] / nMag))) * OC.RAD2DEG;
        if (nVec[1] < 0) raan = 360 - raan;
    }

    let aop = 0;
    if (e > 1e-10 && nMag > 1e-10) {
        aop = Math.acos(Math.min(1, Math.max(-1, dot3(nVec, eVec) / (nMag * e)))) * OC.RAD2DEG;
        if (eVec[2] < 0) aop = 360 - aop;
    }

    let nu = 0;
    if (e > 1e-10) {
        nu = Math.acos(Math.min(1, Math.max(-1, dot3(eVec, r) / (e * rMag)))) * OC.RAD2DEG;
        if (dot3(r, v) < 0) nu = 360 - nu;
    }

    return {
        semi_major_axis_km:      a,
        eccentricity:            e,
        inclination_deg:         incl,
        raan_deg:                raan,
        arg_perigee_deg:         aop,
        true_anomaly_deg:        nu
    };
}

// ─── Kepler's Equation ────────────────────────────────────────────────────────

/** Solve Kepler's equation M = E - e sin(E) for E using Newton-Raphson. */
function solveKepler(M, e, tol = 1e-10) {
    let E = e < 0.8 ? M : Math.PI;
    for (let i = 0; i < 50; i++) {
        const dE = (E - e * Math.sin(E) - M) / (1 - e * Math.cos(E));
        E -= dE;
        if (Math.abs(dE) < tol) break;
    }
    return E;
}

/** Mean anomaly → True anomaly (all radians). */
function meanToTrue(M, e) {
    const E  = solveKepler(M % OC.TWO_PI, e);
    const nu = 2 * Math.atan2(
        Math.sqrt(1 + e) * Math.sin(E / 2),
        Math.sqrt(1 - e) * Math.cos(E / 2)
    );
    return (nu + OC.TWO_PI) % OC.TWO_PI;
}


// ─── Two-Body Propagation ─────────────────────────────────────────────────────

/**
 * Propagate a Keplerian orbit analytically (two-body only).
 * Returns position and velocity in ECI frame.
 *
 * @param {Object} elements - Keplerian elements (all angles in degrees)
 * @param {number} dt - Time step in seconds
 * @returns {{position: number[], velocity: number[], elements: Object}}
 */
function propagateTwoBody(elements, dt) {
    const { semi_major_axis_km: a, eccentricity: e,
            inclination_deg: i, raan_deg: raan,
            arg_perigee_deg: aop, true_anomaly_deg: nu0 } = elements;

    const nuR = nu0 * OC.DEG2RAD;
    const E0  = 2 * Math.atan2(Math.sqrt(1 - e) * Math.sin(nuR / 2),
                               Math.sqrt(1 + e) * Math.cos(nuR / 2));
    const M0  = E0 - e * Math.sin(E0);
    const n   = Math.sqrt(OC.MU / Math.pow(a, 3));   // rad/s
    const M1  = (M0 + n * dt + OC.TWO_PI) % OC.TWO_PI;
    const nu1 = meanToTrue(M1, e) * OC.RAD2DEG;

    const state = keplerianToCartesian(a, e, i, raan, aop, nu1);

    // Compute altitude
    const rMag    = norm3(state.position);
    const altitude = rMag - OC.RE;
    const vMag    = norm3(state.velocity);

    return {
        position_eci:         state.position,
        velocity_eci:         state.velocity,
        altitude_km:          altitude,
        true_anomaly_deg:     nu1,
        velocity_magnitude_km_s: vMag
    };
}

/**
 * Apply J2 secular perturbation rates to Keplerian elements.
 * Updates RAAN and AoP based on time elapsed.
 *
 * @param {Object} elements - {semi_major_axis_km, eccentricity, inclination_deg,
 *                             raan_deg, arg_perigee_deg, true_anomaly_deg}
 * @param {number} dt - Time in seconds
 * @returns {Object} Updated elements
 */
function applyJ2Perturbation(elements, dt) {
    const { semi_major_axis_km: a, eccentricity: e, inclination_deg: iDeg } = elements;
    const i = iDeg * OC.DEG2RAD;
    const p = a * (1 - e * e);
    const n = Math.sqrt(OC.MU / Math.pow(a, 3));

    // J2 secular rates (rad/s) — Vallado (2006) Eq. 9-38
    const factor = -1.5 * n * OC.J2 * Math.pow(OC.RE / p, 2);
    const raanDot = factor * Math.cos(i);
    const aopDot  = factor * (2.5 * Math.sin(i) * Math.sin(i) - 2);

    return Object.assign({}, elements, {
        raan_deg:        elements.raan_deg        + raanDot * dt * OC.RAD2DEG,
        arg_perigee_deg: elements.arg_perigee_deg + aopDot  * dt * OC.RAD2DEG
    });
}

/**
 * Generate orbit animation frames for a given orbit (two-body + J2).
 *
 * @param {Object} params - {semi_major_axis_km, eccentricity, inclination_deg,
 *                           raan_deg, arg_perigee_deg, true_anomaly_deg,
 *                           num_orbits?, steps_per_orbit?}
 * @returns {Object} {frames: Array, period_minutes, total_time_hours}
 */
function generateOrbitFrames(params) {
    const a     = params.semi_major_axis_km     ?? 6778;
    const e     = params.eccentricity           ?? 0.001;
    const i     = params.inclination_deg        ?? 51.6;
    const raan  = params.raan_deg               ?? 0;
    const aop   = params.arg_perigee_deg        ?? 0;
    const nu    = params.true_anomaly_deg       ?? 0;
    const nOrbs = params.num_orbits             ?? 1;
    const steps = params.steps_per_orbit        ?? 360;

    const T      = OC.TWO_PI * Math.sqrt(Math.pow(a, 3) / OC.MU); // seconds
    const totalT = nOrbs * T;
    const dt     = totalT / (nOrbs * steps);
    const nFrames = nOrbs * steps;

    let elements = { semi_major_axis_km: a, eccentricity: e, inclination_deg: i,
                     raan_deg: raan, arg_perigee_deg: aop, true_anomaly_deg: nu };

    const frames = [];
    for (let k = 0; k < nFrames; k++) {
        const t     = k * dt;
        const elJ2  = applyJ2Perturbation(elements, t);
        const frame = propagateTwoBody(elJ2, t);
        frame.frame        = k;
        frame.time_seconds = t;
        frames.push(frame);
    }

    return {
        frames,
        period_minutes: T / 60,
        total_time_hours: totalT / 3600
    };
}


// ─── ECI → Geodetic (lat/lon/alt) ────────────────────────────────────────────

/**
 * Convert ECI position to geodetic latitude, longitude, altitude.
 * Uses simplified spherical Earth (adequate for educational visualisations).
 *
 * @param {number[]} r - ECI position [x,y,z] km
 * @param {number}   t - Seconds since J2000 epoch (for GMST)
 * @returns {{latitude_deg, longitude_deg, altitude_km}}
 */
function eciToGeodetic(r, t) {
    // Greenwich Mean Sidereal Time (simplified)
    const J2000 = Date.UTC(2000, 0, 1, 12, 0, 0);
    const tDays = t / 86400;
    const GMST  = (280.46061837 + 360.98564736629 * tDays) * OC.DEG2RAD;

    const rMag = norm3(r);
    const lat  = Math.asin(r[2] / rMag) * OC.RAD2DEG;
    const lonECI = Math.atan2(r[1], r[0]);
    let   lon   = ((lonECI - GMST) * OC.RAD2DEG + 540) % 360 - 180;

    return {
        latitude_deg:  lat,
        longitude_deg: lon,
        altitude_km:   rMag - OC.RE
    };
}

/**
 * Generate ground track frames for a satellite.
 *
 * @param {Object} params - Same as generateOrbitFrames plus optional t0_unix (ms)
 * @returns {Object} {frames: Array, duration_minutes}
 */
function generateGroundTrack(params) {
    const orbitData = generateOrbitFrames(params);
    const t0 = (params.t0_unix ?? Date.now()) / 1000;   // seconds since Unix epoch

    // Convert Unix time to seconds since J2000
    const J2000unix = Date.UTC(2000, 0, 1, 12, 0, 0) / 1000;
    const t0J2000   = t0 - J2000unix;

    const frames = orbitData.frames.map(f => {
        const geo = eciToGeodetic(f.position_eci, t0J2000 + f.time_seconds);
        return Object.assign({}, f, geo);
    });

    return {
        frames,
        duration_minutes: orbitData.total_time_hours * 60
    };
}


// ─── Hohmann Transfer ─────────────────────────────────────────────────────────

/**
 * Calculate Hohmann transfer between two circular coplanar orbits.
 *
 * @param {number} r1 - Initial orbit radius (km from Earth's centre)
 * @param {number} r2 - Final orbit radius (km from Earth's centre)
 * @returns {Object} Transfer parameters
 */
function hohmannTransfer(r1, r2) {
    if (r1 <= 0 || r2 <= 0) throw new Error('Radii must be positive');
    if (r1 === r2) throw new Error('Orbits must be different');

    const aT = (r1 + r2) / 2;

    const v1   = Math.sqrt(OC.MU / r1);
    const v2   = Math.sqrt(OC.MU / r2);
    const vT1  = Math.sqrt(OC.MU * (2 / r1 - 1 / aT));
    const vT2  = Math.sqrt(OC.MU * (2 / r2 - 1 / aT));

    const dv1   = Math.abs(vT1 - v1);
    const dv2   = Math.abs(v2  - vT2);
    const dvTot = dv1 + dv2;

    const tTransfer  = Math.PI * Math.sqrt(Math.pow(aT, 3) / OC.MU);

    return {
        r1_km:                         r1,
        r2_km:                         r2,
        delta_v1_km_s:                 dv1,
        delta_v2_km_s:                 dv2,
        total_delta_v_km_s:            dvTot,
        transfer_time_seconds:         tTransfer,
        transfer_time_minutes:         tTransfer / 60,
        transfer_time_hours:           tTransfer / 3600,
        transfer_semi_major_axis_km:   aT,
        initial_orbit_velocity_km_s:   v1,
        final_orbit_velocity_km_s:     v2
    };
}


// ─── Perturbation Analysis ────────────────────────────────────────────────────

/**
 * Compute J2, J3, J4 secular perturbation rates and propagate forward.
 *
 * @param {Object} params - Orbital elements + time_seconds + ballistic_coefficient
 * @returns {Object} Initial/final elements and perturbation rates
 */
function advancedPerturbationAnalysis(params) {
    const a    = params.semi_major_axis_km  ?? 6778;
    const e    = params.eccentricity        ?? 0.001;
    const iDeg = params.inclination_deg     ?? 51.6;
    const raan = params.raan_deg            ?? 0;
    const aop  = params.arg_perigee_deg     ?? 0;
    const nu   = params.true_anomaly_deg    ?? 0;
    const dt   = params.time_seconds        ?? 3600;
    const BC   = params.ballistic_coefficient ?? 0.01;  // kg/m²

    const i = iDeg * OC.DEG2RAD;
    const p = a * (1 - e * e);
    const n = Math.sqrt(OC.MU / Math.pow(a, 3));

    // J2 secular rates (deg/day)
    const factorJ2  = -1.5 * n * OC.J2 * Math.pow(OC.RE / p, 2);
    const raanJ2    = factorJ2 * Math.cos(i);
    const aopJ2     = factorJ2 * (2.5 * Math.sin(i) * Math.sin(i) - 2);

    // J3 contribution (first-order approximation)
    const factorJ3  = -1.5 * n * OC.J3 * Math.pow(OC.RE / p, 3);
    const raanJ3    = factorJ3 * Math.cos(i) * (4 - 5 * Math.sin(i) * Math.sin(i));

    // J4 contribution (first-order approximation)
    const factorJ4  = 1.875 * n * OC.J4 * Math.pow(OC.RE / p, 4);
    const raanJ4    = factorJ4 * Math.cos(i) * (1 - 7 / 6 * Math.sin(i) * Math.sin(i));

    const secPerDay = 86400;
    const rates = {
        j2_raan_rate_deg_per_day: raanJ2 * OC.RAD2DEG * secPerDay,
        j2_aop_rate_deg_per_day:  aopJ2  * OC.RAD2DEG * secPerDay,
        j3_contribution_deg_per_day: raanJ3 * OC.RAD2DEG * secPerDay,
        j4_contribution_deg_per_day: raanJ4 * OC.RAD2DEG * secPerDay,
        drag_rate_km_per_day: -OC.SCALE_HEIGHT * OC.RHO0 / BC * 86.4 // simplified
    };

    // Atmospheric drag correction to semi-major axis
    const alt = a - OC.RE;
    const rho = OC.RHO0 * Math.exp(-alt / OC.SCALE_HEIGHT) * 1e9; // kg/km³ → approx
    const v   = Math.sqrt(OC.MU / a);
    const adot = -2 * BC / (rho * v) * 1e-3;  // rough km/s
    const deltaA = adot * dt * 1e-3;           // km change over dt

    const finalElements = {
        semi_major_axis_km:  a + deltaA,
        eccentricity:        e,
        inclination_deg:     iDeg,
        raan_deg:            (raan + raanJ2 * OC.RAD2DEG * dt + raanJ3 * OC.RAD2DEG * dt) % 360,
        arg_perigee_deg:     (aop  + aopJ2  * OC.RAD2DEG * dt) % 360,
        true_anomaly_deg:    nu
    };

    return {
        initial_elements: { semi_major_axis_km: a, eccentricity: e,
                            inclination_deg: iDeg, raan_deg: raan,
                            arg_perigee_deg: aop, true_anomaly_deg: nu },
        final_elements: finalElements,
        perturbation_rates: rates,
        propagation_time_seconds: dt
    };
}


// ─── Launch Window Calculation ────────────────────────────────────────────────

/**
 * Compute launch windows for a target orbit inclination from a launch site.
 * Uses the spherical-Earth launch constraint: cos(i) = cos(φ)·sin(β)
 * where φ is launch-site latitude and β is launch azimuth.
 *
 * @param {Object} params - {launch_site_latitude_deg, launch_site_longitude_deg,
 *                           target_inclination_deg, start_date, num_days}
 * @returns {Object} {windows: Array, ...}
 */
function computeLaunchWindows(params) {
    const lat    = params.launch_site_latitude_deg  ?? 28.5;
    const lon    = params.launch_site_longitude_deg ?? -80.5;
    const incl   = params.target_inclination_deg    ?? 51.6;
    const nDays  = params.num_days ?? 7;
    const startD = params.start_date ? new Date(params.start_date + 'T00:00:00Z')
                                     : new Date();

    // Feasibility check
    if (Math.abs(lat) > incl) {
        return {
            launch_site_latitude_deg:  lat,
            launch_site_longitude_deg: lon,
            target_inclination_deg:    incl,
            start_date: startD.toISOString().split('T')[0],
            num_days:   nDays,
            total_windows: 0,
            windows: [],
            note: `Launch site latitude (${lat}°) exceeds target inclination (${incl}°). No direct-ascent windows exist.`
        };
    }

    // Azimuth for ascending node launch
    const cosAz = Math.cos(incl * OC.DEG2RAD) / Math.cos(lat * OC.DEG2RAD);
    const azAsc = Math.asin(Math.min(1, Math.max(-1, cosAz))) * OC.RAD2DEG;
    const azDesc = 180 - azAsc;  // descending node launch

    const windows = [];

    // Two windows per day (approximately), every 12 hours
    for (let day = 0; day < nDays; day++) {
        for (let half = 0; half < 2; half++) {
            const windowTime = new Date(startD.getTime() +
                                        (day * 24 + half * 12.05) * 3600000);
            const azimuth = half === 0 ? azAsc : azDesc;
            const dv = estimateLaunchDeltaV(lat, incl);

            windows.push({
                datetime:               windowTime.toISOString().replace('.000Z', 'Z'),
                azimuth_deg:            azimuth,
                azimuth_constraint_deg: Math.abs(azimuth),
                delta_v_estimate_km_s:  dv,
                feasible:               true,
                direction:              half === 0 ? 'ascending' : 'descending'
            });
        }
    }

    return {
        launch_site_latitude_deg:  lat,
        launch_site_longitude_deg: lon,
        target_inclination_deg:    incl,
        start_date:   startD.toISOString().split('T')[0],
        num_days:     nDays,
        total_windows: windows.length,
        windows
    };
}

/** Simplified delta-v estimate for launch to orbit (km/s). */
function estimateLaunchDeltaV(lat, incl) {
    const base  = 9.3;                             // km/s baseline LEO
    const earth = 0.465 * Math.cos(lat * OC.DEG2RAD); // Earth's rotation benefit
    const inclPenalty = Math.abs(incl - lat) * 0.005;  // rough penalty
    return base - earth + inclPenalty;
}


// ─── Orbit Catalog ────────────────────────────────────────────────────────────

/** Returns the built-in orbit type catalog (mirrors /orbits/list + /orbits/info). */
function getOrbitCatalog() {
    return [
        {
            id: 'leo',
            name: 'LEO — Low Earth Orbit',
            description: 'Orbits from ~160 km to ~2 000 km altitude. Shortest orbital periods (~90 min), lowest delta-v to reach, strong atmospheric drag.',
            typical_altitude_km: '160–2 000',
            altitude_range_km: [160, 2000],
            typical_eccentricity: '≈ 0',
            typical_inclination_deg: '0–98',
            orbital_period_minutes: '88–127',
            uses: [
                'Human spaceflight (ISS, space stations)',
                'Earth observation & remote sensing',
                'Low-latency broadband (Starlink, OneWeb)',
                'Science missions (Hubble, Fermi)'
            ],
            examples: [
                { name: 'ISS (ZARYA)',             norad: 25544,  country: 'Multinational', altitude_km: 408 },
                { name: 'Hubble Space Telescope',  norad: 20580,  country: 'USA',           altitude_km: 538 },
                { name: 'Starlink-1007',           norad: 44713,  country: 'USA',           altitude_km: 550 },
                { name: 'Landsat 9',               norad: 49260,  country: 'USA',           altitude_km: 705 }
            ]
        },
        {
            id: 'meo',
            name: 'MEO — Medium Earth Orbit',
            description: 'Orbits from ~2 000 km to ~35 786 km. Home of GPS/GNSS constellations and radiation-belt crossing altitude.',
            typical_altitude_km: '2 000–35 786',
            altitude_range_km: [2000, 35786],
            typical_eccentricity: '≈ 0',
            typical_inclination_deg: '55–65',
            orbital_period_minutes: '127–1 436',
            uses: [
                'Navigation (GPS, GLONASS, Galileo, BeiDou)',
                'Communications relay',
                'Radiation belt science (Van Allen Probes)'
            ],
            examples: [
                { name: 'GPS IIF-10 (USA-213)',  norad: 40105, country: 'USA',    altitude_km: 20200 },
                { name: 'Galileo-201',           norad: 37846, country: 'Europe', altitude_km: 23222 },
                { name: 'GLONASS-M 747',         norad: 28921, country: 'Russia', altitude_km: 19130 }
            ]
        },
        {
            id: 'geo',
            name: 'GEO — Geostationary Orbit',
            description: 'Exactly 35 786 km altitude, zero inclination. Satellite appears stationary over one point. 24-hour period.',
            typical_altitude_km: '35 786',
            altitude_range_km: [35586, 35986],
            typical_eccentricity: '< 0.001',
            typical_inclination_deg: '0',
            orbital_period_minutes: '1 436',
            uses: [
                'Weather satellites (GOES, Meteosat)',
                'Broadcast television (DirecTV, SES)',
                'High-speed internet (ViaSat, HughesNet)',
                'Military communications'
            ],
            examples: [
                { name: 'GOES-18',   norad: 51850, country: 'USA',    altitude_km: 35786 },
                { name: 'Intelsat-37e', norad: 41789, country: 'USA', altitude_km: 35786 },
                { name: 'SES-12',    norad: 43488, country: 'Luxembourg', altitude_km: 35786 }
            ]
        },
        {
            id: 'heo',
            name: 'HEO — Highly Elliptical Orbit (Molniya)',
            description: 'Highly elliptical orbit with perigee ~500 km and apogee ~40 000 km. Satellite spends most time near apogee, providing long dwell times over high latitudes.',
            typical_altitude_km: '500–40 000 (apogee)',
            altitude_range_km: [500, 40000],
            typical_eccentricity: '≈ 0.72',
            typical_inclination_deg: '63.4',
            orbital_period_minutes: '~718 (12 h)',
            uses: [
                'Russian Molniya communications satellites',
                'High-latitude coverage',
                'Science (INTEGRAL, XMM-Newton)',
                'Tundra/Sirius broadcast orbits'
            ],
            examples: [
                { name: 'Molniya 3-50',    norad: 25847, country: 'Russia', altitude_km: '38 000 (apogee)' },
                { name: 'INTEGRAL',        norad: 27540, country: 'ESA',    altitude_km: '152 000 (apogee)' },
                { name: 'SiriusXM FM-6',   norad: 39469, country: 'USA',    altitude_km: '47 100 (apogee)' }
            ]
        },
        {
            id: 'sso',
            name: 'SSO — Sun-Synchronous Orbit',
            description: 'Near-polar LEO with retrograde inclination chosen so J2 precession makes the orbital plane precess ~1°/day eastward, matching Earth\'s solar orbit. Passes over a given point at the same local solar time each day.',
            typical_altitude_km: '400–900',
            altitude_range_km: [400, 900],
            typical_eccentricity: '≈ 0',
            typical_inclination_deg: '96–99',
            orbital_period_minutes: '95–103',
            uses: [
                'Earth observation with consistent illumination',
                'Weather (NOAA POES, Metop)',
                'SAR radar (Sentinel-1, TerraSAR-X)',
                'Ocean altimetry (Sentinel-6)'
            ],
            examples: [
                { name: 'Sentinel-2A', norad: 40697, country: 'ESA',  altitude_km: 786 },
                { name: 'Landsat 8',   norad: 39084, country: 'USA',  altitude_km: 705 },
                { name: 'NOAA-20',     norad: 43013, country: 'USA',  altitude_km: 824 }
            ]
        },
        {
            id: 'lagrange',
            name: 'Lagrange Point Orbits (L1/L2)',
            description: 'Halo or Lissajous orbits around the Sun–Earth L1 (1.5M km sunward) or L2 (1.5M km anti-sun). Stable with minimal station-keeping. Ideal for space observatories needing stable thermal environment.',
            typical_altitude_km: '~1 500 000',
            altitude_range_km: [1400000, 1600000],
            typical_eccentricity: 'N/A (halo orbit)',
            typical_inclination_deg: '~0 (ecliptic)',
            orbital_period_minutes: '~175 000 (6 months)',
            uses: [
                'Space observatories (JWST at L2)',
                'Solar monitoring (SOHO, ACE at L1)',
                'Sun–Earth halo science missions'
            ],
            examples: [
                { name: 'James Webb Space Telescope (JWST)', norad: 50463, country: 'USA/ESA/CSA', altitude_km: 1500000 },
                { name: 'SOHO',    norad: 23726, country: 'ESA/NASA', altitude_km: 1500000 },
                { name: 'DSCOVR',  norad: 40390, country: 'USA',      altitude_km: 1500000 }
            ]
        }
    ];
}


// ─── Vector Utilities ─────────────────────────────────────────────────────────

function norm3(v)        { return Math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2]); }
function dot3(a, b)      { return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]; }
function cross3(a, b)    {
    return [
        a[1]*b[2] - a[2]*b[1],
        a[2]*b[0] - a[0]*b[2],
        a[0]*b[1] - a[1]*b[0]
    ];
}


// ─── Public API surface ───────────────────────────────────────────────────────

window.OrbitalCalc = {
    parseTLE,
    keplerianToCartesian,
    cartesianToKeplerian,
    propagateTwoBody,
    applyJ2Perturbation,
    generateOrbitFrames,
    generateGroundTrack,
    eciToGeodetic,
    hohmannTransfer,
    advancedPerturbationAnalysis,
    computeLaunchWindows,
    getOrbitCatalog,
    OC          // constants
};
