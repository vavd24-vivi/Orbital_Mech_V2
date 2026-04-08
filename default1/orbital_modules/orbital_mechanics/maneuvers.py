"""
Orbital Maneuvers and Transfers

Implements common orbital maneuvers:
- Hohmann Transfer
- Bi-elliptic Transfer  
- Simple plane change
- Inclination change

References:
- Curtis, H. D. (2013). "Orbital Mechanics for Engineering Students" (3rd ed.).
- Vallado, D. A., Crawford, P., Hujsak, R., & Kelso, T. S. (2006).
  "Revisiting Spacetrack Report #3: Rev 1". AIAA Paper 2006-6753.
"""

import numpy as np
import math
from .constants import GM_EARTH_KM3_S2, DEG_TO_RAD, RAD_TO_DEG
from .conversions import orbital_velocity


class HohmannTransfer:
    """
    Hohmann Transfer between two circular coplanar orbits.
    
    Transfer Characteristics:
    - Two impulses required
    - Minimum energy transfer between circular orbits
    - Transfer takes half an ellipse period
    - Works for any orbit pair (LEO to GEO, GEO to escape, etc.)
    
    References:
    - Curtis (2013), Section 7.3
    """
    
    def __init__(self, r1, r2, mu=GM_EARTH_KM3_S2):
        """
        Initialize Hohmann transfer.
        
        Parameters
        ----------
        r1 : float
            Initial circular orbit radius (km)
        r2 : float
            Final circular orbit radius (km)
        mu : float
            Gravitational parameter (km³/s²)
        """
        if r1 <= 0 or r2 <= 0:
            raise ValueError("Radii must be positive")
        if r1 == r2:
            raise ValueError("Orbits must be different")
        
        self.r1 = r1
        self.r2 = r2
        self.mu = mu
        
        # Transfer ellipse semi-major axis
        self.a_transfer = (r1 + r2) / 2.0
        
        # Velocities
        self.v1 = orbital_velocity(r1, r1, mu)
        self.v2 = orbital_velocity(r2, r2, mu)
        
        # Transfer orbit velocities at periapis and apoapsis
        self.v_transfer_at_r1 = orbital_velocity(r1, self.a_transfer, mu)
        self.v_transfer_at_r2 = orbital_velocity(r2, self.a_transfer, mu)
    
    def get_delta_v1(self):
        """
        Get first impulse (at initial orbit).
        
        Returns
        -------
        float
            ΔV1 (km/s)
        """
        return abs(self.v_transfer_at_r1 - self.v1)
    
    def get_delta_v2(self):
        """
        Get second impulse (at final orbit).
        
        Returns
        -------
        float
            ΔV2 (km/s)
        """
        return abs(self.v2 - self.v_transfer_at_r2)
    
    def get_total_delta_v(self):
        """
        Get total ΔV for transfer.
        
        Returns
        -------
        float
            Total ΔV (km/s)
        """
        return self.get_delta_v1() + self.get_delta_v2()
    
    def get_transfer_time(self):
        """
        Get transfer time (half ellipse period).
        
        Returns
        -------
        float
            Transfer time (seconds)
        """
        transfer_period = 2 * math.pi * math.sqrt(self.a_transfer**3 / self.mu)
        return transfer_period / 2.0
    
    def to_dict(self):
        """Return summary dictionary."""
        return {
            'r1_km': self.r1,
            'r2_km': self.r2,
            'delta_v1_km_s': self.get_delta_v1(),
            'delta_v2_km_s': self.get_delta_v2(),
            'total_delta_v_km_s': self.get_total_delta_v(),
            'transfer_time_seconds': self.get_transfer_time(),
            'transfer_time_hours': self.get_transfer_time() / 3600.0,
            'transfer_semi_major_axis_km': self.a_transfer
        }


class BiellipticTransfer:
    """
    Bi-elliptic Transfer between two circular coplanar orbits.
    
    Transfer Characteristics:
    - Three impulses required (or two if starting/ending at infinity)
    - Can be more efficient than Hohmann for large radius ratios (r2/r1 > 11.94)
    - Takes longer than Hohmann transfer
    - Used for high-energy transfers (e.g., Earth to Mars)
    
    References:
    - Curtis (2013), Section 7.4
    """
    
    def __init__(self, r1, r2, r_intermediate=None, mu=GM_EARTH_KM3_S2):
        """
        Initialize bi-elliptic transfer.
        
        Parameters
        ----------
        r1 : float
            Initial circular orbit radius (km)
        r2 : float
            Final circular orbit radius (km)
        r_intermediate : float, optional
            Intermediate apoapsis radius. If None, uses optimal value.
        mu : float
            Gravitational parameter (km³/s²)
        """
        self.r1 = r1
        self.r2 = r2
        self.mu = mu
        
        # Optimal intermediate radius (maximizes energy at infinity ratio)
        if r_intermediate is None:
            # For maximum efficiency, typically 1.5-2x r2
            self.r_intermediate = 1.5 * r2
        else:
            self.r_intermediate = r_intermediate
        
        # Transfer ellipse 1: r1 to r_intermediate
        self.a_transfer1 = (r1 + self.r_intermediate) / 2.0
        
        # Transfer ellipse 2: r_intermediate to r2  
        self.a_transfer2 = (self.r_intermediate + r2) / 2.0
        
        # Velocities in circular orbits
        self.v1 = orbital_velocity(r1, r1, mu)
        self.v2 = orbital_velocity(r2, r2, mu)
        
        # Transfer orbit velocities
        self.v_transfer1_at_r1 = orbital_velocity(r1, self.a_transfer1, mu)
        self.v_intermediate_from_1 = orbital_velocity(self.r_intermediate, self.a_transfer1, mu)
        self.v_intermediate_from_2 = orbital_velocity(self.r_intermediate, self.a_transfer2, mu)
        self.v_transfer2_at_r2 = orbital_velocity(r2, self.a_transfer2, mu)
    
    def get_delta_v1(self):
        """First impulse (leave initial orbit)."""
        return abs(self.v_transfer1_at_r1 - self.v1)
    
    def get_delta_v2(self):
        """Second impulse (at intermediate altitude)."""
        return abs(self.v_intermediate_from_2 - self.v_intermediate_from_1)
    
    def get_delta_v3(self):
        """Third impulse (enter final orbit)."""
        return abs(self.v2 - self.v_transfer2_at_r2)
    
    def get_total_delta_v(self):
        """Total ΔV for transfer."""
        return self.get_delta_v1() + self.get_delta_v2() + self.get_delta_v3()
    
    def get_transfer_time(self):
        """Total transfer time (both ellipses)."""
        period1 = math.pi * math.sqrt(self.a_transfer1**3 / self.mu)
        period2 = math.pi * math.sqrt(self.a_transfer2**3 / self.mu)
        return period1 + period2
    
    def to_dict(self):
        """Return summary dictionary."""
        return {
            'r1_km': self.r1,
            'r2_km': self.r2,
            'r_intermediate_km': self.r_intermediate,
            'delta_v1_km_s': self.get_delta_v1(),
            'delta_v2_km_s': self.get_delta_v2(),
            'delta_v3_km_s': self.get_delta_v3(),
            'total_delta_v_km_s': self.get_total_delta_v(),
            'transfer_time_seconds': self.get_transfer_time(),
            'transfer_time_hours': self.get_transfer_time() / 3600.0
        }


class PlaneChange:
    """
    Simple plane change maneuver in circular orbit.
    
    Maneuver Characteristics:
    - Single impulse
    - Changes orbital inclination only
    - Most efficient at apoapsis
    - Can be combined with Hohmann transfer
    
    References:
    - Curtis (2013), Section 7.5
    """
    
    def __init__(self, r, delta_i, mu=GM_EARTH_KM3_S2):
        """
        Initialize plane change.
        
        Parameters
        ----------
        r : float
            Circular orbit radius (km)
        delta_i : float
            Inclination change (radians)
        mu : float
            Gravitational parameter (km³/s²)
        """
        self.r = r
        self.delta_i = delta_i
        self.mu = mu
        
        # Orbital velocity
        self.v = orbital_velocity(r, r, mu)
    
    def get_delta_v_simple(self):
        """
        Simple plane change (perpendicular impulse).
        
        ΔV = 2 * v * sin(Δi/2)
        
        Returns
        -------
        float
            ΔV magnitude (km/s)
        """
        return 2 * self.v * math.sin(self.delta_i / 2)
    
    def get_delta_v_hohmann_combined(self, r_intermediate):
        """
        Plane change combined with Hohmann transfer.
        
        More efficient than pure plane change for large orbits.
        
        Parameters
        ----------
        r_intermediate : float
            Intermediate orbit radius for better efficiency (usually apoapsis)
        
        Returns
        -------
        float
            ΔV magnitude (km/s)
        """
        # Velocity at intermediate orbit
        v_intermediate = orbital_velocity(r_intermediate, r_intermediate, self.mu)
        
        # Plane change at intermediate orbit is more efficient
        return 2 * v_intermediate * math.sin(self.delta_i / 2)


class OrbitalManeuverSequence:
    """
    Sequence of orbital maneuvers with combined ΔV calculation.
    """
    
    def __init__(self):
        """Initialize empty maneuver sequence."""
        self.maneuvers = []
        self.total_delta_v = 0.0
        self.total_time = 0.0
    
    def add_hohmann_transfer(self, r1, r2, mu=GM_EARTH_KM3_S2):
        """Add Hohmann transfer to sequence."""
        transfer = HohmannTransfer(r1, r2, mu)
        self.maneuvers.append({
            'type': 'hohmann',
            'data': transfer.to_dict()
        })
        self.total_delta_v += transfer.get_total_delta_v()
        self.total_time += transfer.get_transfer_time()
    
    def add_plane_change(self, r, delta_i, mu=GM_EARTH_KM3_S2):
        """Add plane change to sequence."""
        maneuver = PlaneChange(r, delta_i, mu)
        self.maneuvers.append({
            'type': 'plane_change',
            'delta_v': maneuver.get_delta_v_simple(),
            'delta_i_deg': delta_i * RAD_TO_DEG
        })
        self.total_delta_v += maneuver.get_delta_v_simple()
    
    def get_summary(self):
        """Get summary of maneuver sequence."""
        return {
            'maneuvers': self.maneuvers,
            'total_delta_v_km_s': self.total_delta_v,
            'total_time_seconds': self.total_time,
            'total_time_hours': self.total_time / 3600.0
        }
