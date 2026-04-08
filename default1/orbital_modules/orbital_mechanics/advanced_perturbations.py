"""
Advanced Perturbations: J3, J4, and Atmospheric Drag

Extends orbital propagation with higher-order perturbations and drag effects.

References:
- Vallado, D. A., Crawford, P., Hujsak, R., & Kelso, T. S. (2006).
  "Revisiting Spacetrack Report #3: Rev 1". AIAA Paper 2006-6753.
- Curtis, H. D. (2013). "Orbital Mechanics for Engineering Students" (3rd ed.).
- Anselmo, L., & Pardini, C. (2016). "Updated MASTER model for LDEM calculations."
"""

import numpy as np
import math
from .constants import (
    J2, J3, J4, EARTH_RADIUS_KM, GM_EARTH_KM3_S2,
    SCALE_HEIGHT_KM
)
from .conversions import cartesian_to_keplerian, keplerian_to_cartesian


class AdvancedPerturbationPropagator:
    """
    Propagator including J2, J3, J4 perturbations and atmospheric drag.
    
    More accurate than J2-only propagator for medium-term predictions.
    
    Limitations:
    - Still analytical approximation
    - Best for LEO (high atmospheric drag)
    - Less accurate for GEO/high altitude
    """
    
    def __init__(self, a, e, i, omega_cap, omega, nu, 
                 mu=GM_EARTH_KM3_S2, j2=J2, j3=J3, j4=J4,
                 re=EARTH_RADIUS_KM, include_drag=True, ballistic_coefficient=0.01):
        """
        Initialize advanced perturbation propagator.
        
        Parameters
        ----------
        a, e, i, omega_cap, omega, nu : float
            Keplerian elements
        mu : float
            Gravitational parameter
        j2, j3, j4 : float
            Zonal harmonic coefficients
        re : float
            Earth radius
        include_drag : bool
            Include atmospheric drag
        ballistic_coefficient : float
            Ballistic coefficient B* from TLE (kg/m²)
        """
        self.a = a
        self.e = e
        self.i = i
        self.omega_cap = omega_cap
        self.omega = omega
        self.nu = nu
        self.mu = mu
        self.j2 = j2
        self.j3 = j3
        self.j4 = j4
        self.re = re
        self.include_drag = include_drag
        self.b_star = ballistic_coefficient
        
        # Precompute rates
        self._compute_perturbation_rates()
    
    def _compute_perturbation_rates(self):
        """Compute time-averaged perturbation rates."""
        n = np.sqrt(self.mu / self.a**3)  # Mean motion
        p = self.a * (1 - self.e**2)
        
        cos_i = np.cos(self.i)
        sin_i = np.sin(self.i)
        
        # J2 rates
        factor_j2 = (3/2) * self.j2 * n * (self.re / p)**2
        
        self.d_omega_cap_dt_j2 = -factor_j2 * cos_i
        self.d_omega_dt_j2 = factor_j2 * (5 * cos_i**2 - 1) / 2
        self.d_nu_dt_j2 = factor_j2 * (1 - 1.5 * cos_i**2) / 2  # Mean motion perturbation
        
        # J3 rates (more subtle, affects $\omega$ and $\Omega$)
        if abs(self.j3) > 1e-10:
            factor_j3 = (self.j3 * n * (self.re / p)**3 / 8)
            
            self.d_omega_cap_dt_j3 = -factor_j3 * sin_i * (5 * cos_i**2 - 1)
            self.d_omega_dt_j3 = factor_j3 * sin_i**2 * (7 * cos_i**2 - 1)
            self.d_m_dt_j3 = factor_j3 * sin_i * (4 - 5 * sin_i**2) * self.e
        else:
            self.d_omega_cap_dt_j3 = 0
            self.d_omega_dt_j3 = 0
            self.d_m_dt_j3 = 0
        
        # J4 rates (very small but non-zero)
        if abs(self.j4) > 1e-10:
            factor_j4 = -(self.j4 * n * (self.re / p)**4 / 3)
            
            self.d_omega_dt_j4 = factor_j4 * (1 - 7 * cos_i**2 + 56 * cos_i**4 / 3)
        else:
            self.d_omega_dt_j4 = 0
        
        # Atmospheric drag
        self.d_a_dt_drag = 0
        self.d_e_dt_drag = 0
        
        if self.include_drag and self.e < 1.0:  # Only for bound orbits
            # Drag acceleration (simplified)
            # a_drag = -0.5 * ρ * v² * (Cd * A / m)
            # For TLE, approximate using b_star
            
            rho_scale_height = SCALE_HEIGHT_KM
            
            # Exponential atmosphere model
            altitude = self.a - self.re
            if altitude > 0:
                rho = rho_scale_height * np.exp(-altitude / 70)  # ~70 km scale height
            else:
                rho = 0
            
            # Drag coefficient (conservative estimate)
            cd = 2.2
            area_to_mass = 0.004  # m²/kg (typical for satellites)
            
            # Drag effect on semi-major axis
            v_circ = np.sqrt(self.mu / self.a)  # Circular velocity
            drag_accel = 0.5 * rho * v_circ**2 * cd * area_to_mass
            
            self.d_a_dt_drag = -2 * self.a**2 * drag_accel / self.mu
            self.d_e_dt_drag = -5 * self.a * self.e * drag_accel / (2 * self.mu) if self.e > 0 else 0
    
    def propagate(self, dt):
        """
        Propagate orbit forward by dt seconds with all perturbations.
        
        Parameters
        ----------
        dt : float
            Time step (seconds)
        
        Returns
        -------
        dict
            Updated Keplerian elements
        """
        # Semi-major axis (J2 has no first-order effect)
        a_new = self.a + self.d_a_dt_drag * dt
        
        # Eccentricity (J2 has no first-order effect)
        e_new = max(0, self.e + self.d_e_dt_drag * dt)
        
        # Inclination (J2, J3, J4 have no first-order effect)
        i_new = self.i
        
        # RAAN (J2 + J3)
        omega_cap_new = self.omega_cap + (self.d_omega_cap_dt_j2 + self.d_omega_cap_dt_j3) * dt
        
        # Argument of perigee (J2 + J3 + J4)
        omega_new = self.omega + (self.d_omega_dt_j2 + self.d_omega_dt_j3 + self.d_omega_dt_j4) * dt
        
        # True anomaly (includes mean motion and J3 effect)
        n = np.sqrt(self.mu / self.a**3)
        nu_new = self.nu + (n + self.d_nu_dt_j2 + self.d_m_dt_j3) * dt
        
        return {
            'a': a_new,
            'e': e_new,
            'i': i_new,
            'omega_cap': omega_cap_new,
            'omega': omega_new,
            'nu': nu_new
        }
    
    def get_perturbation_summary(self):
        """Get summary of all perturbation rates."""
        return {
            'raan_precession_deg_per_day': (self.d_omega_cap_dt_j2 + self.d_omega_cap_dt_j3) * 86164.0905 * 180 / np.pi,
            'omega_advance_deg_per_day': (self.d_omega_dt_j2 + self.d_omega_dt_j3 + self.d_omega_dt_j4) * 86164.0905 * 180 / np.pi,
            'mean_motion_perturb_deg_per_day': (self.d_nu_dt_j2 + self.d_m_dt_j3) * 86164.0905 * 180 / np.pi,
            'semi_major_axis_decay_km_per_day': self.d_a_dt_drag * 86400,
            'eccentricity_change_per_day': self.d_e_dt_drag * 86400,
            'j2_enabled': True,
            'j3_enabled': abs(self.j3) > 1e-10,
            'j4_enabled': abs(self.j4) > 1e-10,
            'drag_enabled': self.include_drag
        }


class AtmosphericDragModel:
    """
    Atmospheric density model for drag calculations.
    """
    
    # Density at various altitudes (from standard atmosphere)
    DENSITY_TABLE = {
        100: 4.99e-6,    # kg/m³
        120: 1.63e-6,
        150: 2.83e-7,
        200: 2.54e-8,
        300: 3.35e-10,
        500: 1.54e-11,
        700: 3.01e-12,
        1000: 3.56e-13
    }
    
    @staticmethod
    def get_density(altitude_km):
        """
        Get atmospheric density at given altitude (exponential model).
        
        Parameters
        ----------
        altitude_km : float
            Altitude above sea level (km)
        
        Returns
        -------
        float
            Density (kg/m³)
        """
        if altitude_km < 100:
            return 1.225  # Sea level density
        
        if altitude_km > 1000:
            return 1e-15  # Negligible
        
        # Find surrounding altitudes in table
        altitudes = sorted(AtmosphericDragModel.DENSITY_TABLE.keys())
        
        for i in range(len(altitudes) - 1):
            if altitudes[i] <= altitude_km <= altitudes[i + 1]:
                h1, h2 = altitudes[i], altitudes[i + 1]
                rho1 = AtmosphericDragModel.DENSITY_TABLE[h1]
                rho2 = AtmosphericDragModel.DENSITY_TABLE[h2]
                
                # Logarithmic interpolation (atmosphere is exponential)
                if rho1 > 0:
                    rho = rho1 * np.exp((np.log(rho2 / rho1) / (h2 - h1)) * (altitude_km - h1))
                else:
                    rho = rho2
                
                return max(rho, 1e-15)
        
        return 1e-15
    
    @staticmethod
    def calculate_drag_acceleration(velocity_mag, altitude_km, cd=2.2, A_over_m=0.004):
        """
        Calculate atmospheric drag acceleration.
        
        Parameters
        ----------
        velocity_mag : float
            Velocity magnitude (km/s)
        altitude_km : float
            Altitude (km)
        cd : float
            Drag coefficient
        A_over_m : float
            Area-to-mass ratio (m²/kg)
        
        Returns
        -------
        float
            Drag acceleration (km/s²)
        """
        rho = AtmosphericDragModel.get_density(altitude_km)
        v_m_s = velocity_mag * 1000  # Convert km/s to m/s
        
        # Drag acceleration: a_drag = -0.5 * ρ * Cd * (A/m) * v²
        a_drag = -0.5 * rho * cd * A_over_m * v_m_s**2
        
        return a_drag / 1000  # Return in km/s²


class LaunchWindowOptimizer:
    """
    Optimize launch window for minimum energy transfer.
    
    Finds optimal launch time to achieve target orbit with minimum ΔV.
    """
    
    def __init__(self, launch_site_lat, launch_site_lon, target_orbit_params):
        """
        Initialize launch window optimizer.
        
        Parameters
        ----------
        launch_site_lat : float
            Launch site latitude (degrees)
        launch_site_lon : float
            Launch site longitude (degrees)
        target_orbit_params : dict
            Target orbit parameters (a, e, i, etc.)
        """
        self.launch_site_lat = launch_site_lat
        self.launch_site_lon = launch_site_lon
        self.target_orbit = target_orbit_params
    
    def compute_launch_windows(self, start_date, num_days=7):
        """
        Compute optimal launch windows over a time period.
        
        Parameters
        ----------
        start_date : datetime
            Start date for analysis
        num_days : int
            Number of days to analyze
        
        Returns
        -------
        list
            List of launch window opportunities
        """
        windows = []
        
        # Earth rotation period (sidereal day)
        sidereal_day = 86164.0905  # seconds
        
        # Analyze multiple launch opportunities
        for day in range(num_days):
            # Launch site rotates around Earth
            # Optimal azimuth depends on target inclination and launch site latitude
            
            target_inclination = self.target_orbit.get('i', 51.6)
            
            # Azimuth constraints from launch site
            # Can't reach inclination less than launch site latitude
            if self.launch_site_lat > target_inclination:
                continue  # Impossible from this site
            
            # Calculate launch azimuth
            cos_azimuth = np.cos(target_inclination * np.pi / 180) / \
                         np.cos(self.launch_site_lat * np.pi / 180)
            
            if abs(cos_azimuth) > 1:
                continue  # Geometrically impossible
            
            azimuth = np.arccos(cos_azimuth) * 180 / np.pi
            
            # Launch window occurs twice per day (north and south divergences)
            for azimuth_option in [azimuth, 360 - azimuth]:
                # Rough energy estimate (simplified)
                delta_v_estimate = 10  # km/s baseline
                
                windows.append({
                    'date': start_date + np.timedelta64(day, 'D'),
                    'azimuth_deg': azimuth_option,
                    'inclination_achievable_deg': target_inclination,
                    'delta_v_estimate_km_s': delta_v_estimate,
                    'notes': f"Launch day {day+1}, azimuth {azimuth_option:.1f}°"
                })
        
        return windows
