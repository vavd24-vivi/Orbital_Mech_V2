"""
Orbital Propagators: Two-Body, J2-Perturbed, and SGP4

Implements various propagation methods for orbital analysis and prediction.

References:
- Vallado, D. A., Crawford, P., Hujsak, R., & Kelso, T. S. (2006).
  "Revisiting Spacetrack Report #3: Rev 1". AIAA Paper 2006-6753.
- Curtis, H. D. (2013). "Orbital Mechanics for Engineering Students" (3rd ed.).
"""

import numpy as np
import math
from .constants import (
    GM_EARTH_KM3_S2, J2, J3, GM_SUN_KM3_S2, EARTH_RADIUS_KM,
    DEG_TO_RAD, RAD_TO_DEG
)
from .conversions import (
    cartesian_to_keplerian, keplerian_to_cartesian,
    orbital_period
)


class TwoBodyPropagator:
    """
    Classical two-body propagator (Keplerian orbit).
    
    Assumes:
    - Spherically symmetric central body
    - No perturbations (J2, atmospheric drag, etc.)
    - No third-body effects
    
    Good for:
    - Educational purposes
    - Quick orbit estimation
    - High-level mission planning
    
    Limitations:
    - Accumulating errors over time
    - No realistic orbit decay or precession
    """
    
    def __init__(self, r_vec, v_vec, mu=GM_EARTH_KM3_S2):
        """
        Initialize propagator with initial state vectors.
        
        Parameters
        ----------
        r_vec : array_like
            Position vector [x, y, z] (km)
        v_vec : array_like
            Velocity vector [vx, vy, vz] (km/s)
        mu : float
            Gravitational parameter (km³/s²)
        """
        self.r_vec = np.array(r_vec, dtype=float)
        self.v_vec = np.array(v_vec, dtype=float)
        self.mu = mu
        
        # Store initial Keplerian elements
        self.kep = cartesian_to_keplerian(self.r_vec, self.v_vec, mu)
        self.period = orbital_period(self.kep['a'], mu)
    
    def propagate(self, dt):
        """
        Propagate orbit forward by dt seconds (simple numerical integration).
        
        Parameters
        ----------
        dt : float
            Time step (seconds)
        
        Returns
        -------
        tuple
            (r_vec, v_vec) at time t0 + dt
        
        Notes
        -----
        Uses adaptive Runge-Kutta 4th/5th order method (DOP853)
        """
        from scipy.integrate import solve_ivp
        
        def derivatives(t, state):
            r = state[:3]
            v = state[3:]
            r_mag = np.linalg.norm(r)
            accel = -self.mu / r_mag**3 * r
            return np.concatenate([v, accel])
        
        state0 = np.concatenate([self.r_vec, self.v_vec])
        
        sol = solve_ivp(derivatives, [0, dt], state0, method='DOP853', dense_output=True)
        
        if sol.t[-1] < dt * 0.99:
            print(f"Warning: Integration stopped early at t={sol.t[-1]}")
        
        final_state = sol.y[:, -1]
        return final_state[:3], final_state[3:]
    
    def propagate_to_periapsis(self):
        """
        Propagate to next periapsis crossing.
        
        Returns
        -------
        tuple
            (r_vec, v_vec, time_to_periapsis)
        """
        # If we're already near periapsis, go to next one
        nu = self.kep['nu']
        target_nu = 0.0
        
        if nu > math.pi / 2:
            # Coming back from apoapsis, go to next periapsis
            dnu = 2 * math.pi - nu
        else:
            dnu = -nu if nu > 0 else 0
        
        # Time for this true anomaly change
        # Approximately: dt = dnu / mean_motion
        mean_motion_rad_s = 2 * math.pi / self.period
        dt = dnu / mean_motion_rad_s
        
        r_vec, v_vec = self.propagate(dt)
        return r_vec, v_vec, dt


class J2Propagator:
    """
    J2-perturbed propagator (linearized perturbation analysis).
    
    Includes effects of Earth's oblateness (J2 term) on:
    - Right Ascension of Ascending Node (RAAN) precession
    - Argument of Perigee (ω) regression/advance
    
    Good for:
    - Medium-term predictions (days to weeks)
    - Understanding orbit precession
    - Sun-synchronous orbit calculations
    
    Limitations:
    - Only linearized J2 effects
    - Ignores J3, J4 and higher terms
    - Ignores atmospheric drag and third-body perturbations
    - Accuracy degrades over days/weeks
    """
    
    def __init__(self, a, e, i, omega_cap, omega, nu, mu=GM_EARTH_KM3_S2, j2=J2, re=EARTH_RADIUS_KM):
        """
        Initialize J2 propagator with Keplerian elements.
        
        Parameters
        ----------
        a : float
            Semi-major axis (km)
        e : float
            Eccentricity
        i : float
            Inclination (radians)
        omega_cap : float
            RAAN (radians)
        omega : float
            Argument of perigee (radians)
        nu : float
            True anomaly (radians)
        mu : float
            Gravitational parameter (km³/s²)
        j2 : float
            J2 coefficient
        re : float
            Earth radius (km)
        """
        self.a = a
        self.e = e
        self.i = i
        self.omega_cap = omega_cap
        self.omega = omega
        self.nu = nu
        self.mu = mu
        self.j2 = j2
        self.re = re
        
        # Precompute J2 perturbation rates
        self._compute_perturbation_rates()
    
    def _compute_perturbation_rates(self):
        """Compute time-averaged perturbation rates (rad/s)."""
        n = np.sqrt(self.mu / self.a**3)  # Mean motion (rad/s)
        p = self.a * (1 - self.e**2)
        
        # RAAN precession rate
        self.d_omega_cap_dt = (-3/2 * self.j2 * n * 
                               (self.re / p)**2 * np.cos(self.i))
        
        # Argument of perigee regression/advance
        self.d_omega_dt = (3/4 * self.j2 * n * 
                          (self.re / p)**2 * (5 * np.cos(self.i)**2 - 1))
        
        # Semi-major axis: J2 has no first-order effect
        self.d_a_dt = 0.0
        
        # Eccentricity: J2 has no first-order effect
        self.d_e_dt = 0.0
        
        # Inclination: J2 has no first-order effect
        self.d_i_dt = 0.0
    
    def propagate(self, dt):
        """
        Propagate orbit forward by dt seconds using linearized J2 perturbation.
        
        Parameters
        ----------
        dt : float
            Time step (seconds)
        
        Returns
        -------
        dict
            Updated Keplerian elements
        """
        a_new = self.a + self.d_a_dt * dt
        e_new = self.e + self.d_e_dt * dt
        i_new = self.i + self.d_i_dt * dt
        omega_cap_new = self.omega_cap + self.d_omega_cap_dt * dt
        omega_new = self.omega + self.d_omega_dt * dt
        
        # True anomaly changes with mean motion (plus J2 effects)
        n = np.sqrt(self.mu / self.a**3)
        nu_new = self.nu + n * dt
        
        return {
            'a': a_new,
            'e': e_new,
            'i': i_new,
            'omega_cap': omega_cap_new,
            'omega': omega_new,
            'nu': nu_new
        }
    
    def get_raan_precession_rate_deg_per_day(self):
        """
        Get RAAN precession rate in degrees per day.
        
        Returns
        -------
        float
            RAAN precession rate (degrees per sidereal day)
        """
        return self.d_omega_cap_dt * 86164.0905 * RAD_TO_DEG
    
    def get_apsidal_advance_rate_deg_per_day(self):
        """
        Get argument of perigee advance rate in degrees per day.
        
        Returns
        -------
        float
            Argument of perigee rate (degrees per sidereal day)
        """
        return self.d_omega_dt * 86164.0905 * RAD_TO_DEG


class SGP4Wrapper:
    """
    Wrapper around sgp4 library for TLE-based propagation.
    
    SGP4/SDP4 is the standard propagator for LEO and GEO objects.
    
    Good for:
    - Accurate short-term predictions (hours to days)
    - TLE-based propagation
    - Comparison with official NORAD predictions
    
    Limitations:
    - Accuracy limited by TLE age
    - Tuned for tracking, not high-precision prediction
    - Cannot propagate beyond valid TLE date range
    """
    
    def __init__(self, tle):
        """
        Initialize SGP4 propagator from TLE.
        
        Parameters
        ----------
        tle : TLE
            Two-Line Element object from tle module
        """
        from sgp4.api import Satrec
        
        self.tle = tle
        
        # Initialize satellite with SGP4
        self.sat = Satrec.twoline2rv(tle.line1, tle.line2)
        
        if self.sat.error != 0:
            raise ValueError(f"SGP4 initialization error: {self.sat.error}")
    
    def propagate_dt(self, dt_seconds):
        """
        Propagate from TLE epoch by dt_seconds.
        
        Parameters
        ----------
        dt_seconds : float
            Seconds since TLE epoch
        
        Returns
        -------
        dict
            Position and velocity in ECI TEME frame
        """
        from sgp4.api import jday
        
        # Add dt to epoch
        epoch_dt = self.tle.epoch_datetime
        new_dt = epoch_dt + np.timedelta64(int(dt_seconds), 's')
        
        jd = jday(new_dt.year, new_dt.month, new_dt.day, 
                  new_dt.hour, new_dt.minute, new_dt.second)
        fr = new_dt.microsecond / 1e6
        
        err, r, v = self.sat.sgp4(jd, fr)
        
        if err != 0:
            raise RuntimeError(f"SGP4 propagation error: {err}")
        
        return {
            'position_km': r,
            'velocity_km_s': v,
            'datetime': new_dt.isoformat()
        }


def compare_propagators(r_vec, v_vec, time_array_seconds, include_sgp4=False, tle=None):
    """
    Compare propagation methods over time.
    
    Parameters
    ----------
    r_vec : array_like
        Initial position (km)
    v_vec : array_like
        Initial velocity (km/s)
    time_array_seconds : array_like
        Times to propagate to (seconds)
    include_sgp4 : bool, optional
        Include SGP4 comparison (requires tle parameter)
    tle : TLE, optional
        TLE object for SGP4 propagation
    
    Returns
    -------
    dict
        Results from each propagation method
    """
    results = {}
    
    # Two-body propagation
    two_body_prop = TwoBodyPropagator(r_vec, v_vec)
    results['two_body'] = []
    
    for t in time_array_seconds:
        r, v = two_body_prop.propagate(t)
        results['two_body'].append({'r': r, 'v': v, 't': t})
    
    # J2 propagation
    kep = cartesian_to_keplerian(r_vec, v_vec)
    j2_prop = J2Propagator(kep['a'], kep['e'], kep['i'], 
                          kep['omega_cap'], kep['omega'], kep['nu'])
    results['j2'] = []
    
    for t in time_array_seconds:
        kep_new = j2_prop.propagate(t)
        r, v = keplerian_to_cartesian(kep_new['a'], kep_new['e'], kep_new['i'],
                                      kep_new['omega_cap'], kep_new['omega'], 
                                      kep_new['nu'])
        results['j2'].append({'r': r, 'v': v, 't': t})
    
    # SGP4 propagation (if available)
    if include_sgp4 and tle is not None:
        try:
            sgp4_prop = SGP4Wrapper(tle)
            results['sgp4'] = []
            for t in time_array_seconds:
                result = sgp4_prop.propagate_dt(t)
                results['sgp4'].append(result)
        except Exception as e:
            results['sgp4_error'] = str(e)
    
    return results
