"""
State Vector and Keplerian Element Conversions

This module implements bidirectional conversions between:
- Cartesian State Vectors: (r, v) - position and velocity vectors
- Keplerian Elements: (a, e, i, Ω, ω, ν) - orbital parameters

References:
- Vallado, D. A., Crawford, P., Hujsak, R., & Kelso, T. S. (2006).
  "Revisiting Spacetrack Report #3: Rev 1". AIAA Paper 2006-6753.
- Curtis, H. D. (2013). "Orbital Mechanics for Engineering Students" (3rd ed.).
  Butterworth-Heinemann. ISBN 978-0-08-102133-0.
"""

import numpy as np
import math
from .constants import GM_EARTH_KM3_S2, DEG_TO_RAD, RAD_TO_DEG


def cartesian_to_keplerian(r_vec, v_vec, mu=GM_EARTH_KM3_S2):
    """
    Convert Cartesian state vectors to Keplerian elements.
    
    Parameters
    ----------
    r_vec : array_like
        Position vector [x, y, z] in km
    v_vec : array_like
        Velocity vector [vx, vy, vz] in km/s
    mu : float, optional
        Gravitational parameter (km³/s²). Default: Earth
    
    Returns
    -------
    dict
        Dictionary containing Keplerian elements:
        - a : Semi-major axis (km)
        - e : Eccentricity
        - i : Inclination (radians)
        - omega_cap : RAAN - Right Ascension of Ascending Node (radians)
        - omega : Argument of Perigee (radians)
        - nu : True Anomaly (radians)
    
    Notes
    -----
    Implementation follows Curtis (2013) Algorithm 4.1
    Handles circular and equatorial orbit edge cases
    """
    r_vec = np.array(r_vec, dtype=float)
    v_vec = np.array(v_vec, dtype=float)
    
    r = np.linalg.norm(r_vec)
    v = np.linalg.norm(v_vec)
    
    # Specific angular momentum
    h_vec = np.cross(r_vec, v_vec)
    h = np.linalg.norm(h_vec)
    
    # Specific orbital energy
    xi = (v**2 / 2.0) - (mu / r)
    
    # Semi-major axis
    if abs(xi) < 1e-14:  # Parabolic orbit
        a = float('inf')
    else:
        a = -mu / (2.0 * xi)
    
    # Eccentricity vector
    e_vec = ((v**2 - mu/r) * r_vec - np.dot(r_vec, v_vec) * v_vec) / mu
    e = np.linalg.norm(e_vec)
    
    # Inclination
    i = math.acos(min(1.0, max(-1.0, h_vec[2] / h)))
    
    # Ascending node
    n_vec = np.cross(np.array([0, 0, 1]), h_vec)
    n = np.linalg.norm(n_vec)
    
    if n < 1e-10:  # Equatorial orbit
        omega_cap = 0.0
    else:
        omega_cap = math.acos(min(1.0, max(-1.0, n_vec[0] / n)))
        if n_vec[1] < 0:
            omega_cap = 2 * math.pi - omega_cap
    
    # Argument of perigee
    if e < 1e-10:  # Circular orbit
        omega = 0.0
    else:
        cos_omega = np.dot(n_vec, e_vec) / (n * e)
        omega = math.acos(min(1.0, max(-1.0, cos_omega)))
        if e_vec[2] < 0:
            omega = 2 * math.pi - omega
    
    # True anomaly
    if e < 1e-10:  # Circular orbit
        cos_nu = np.dot(n_vec, r_vec) / (n * r)
    else:
        cos_nu = np.dot(e_vec, r_vec) / (e * r)
    
    nu = math.acos(min(1.0, max(-1.0, cos_nu)))
    if np.dot(r_vec, v_vec) < 0:
        nu = 2 * math.pi - nu
    
    return {
        'a': a,
        'e': e,
        'i': i,
        'omega_cap': omega_cap,  # RAAN
        'omega': omega,  # Argument of perigee
        'nu': nu  # True anomaly
    }


def keplerian_to_cartesian(a, e, i, omega_cap, omega, nu, mu=GM_EARTH_KM3_S2):
    """
    Convert Keplerian elements to Cartesian state vectors.
    
    Parameters
    ----------
    a : float
        Semi-major axis (km)
    e : float
        Eccentricity (0 <= e < 1 for elliptical orbits)
    i : float
        Inclination (radians)
    omega_cap : float
        Right Ascension of Ascending Node (radians)
    omega : float
        Argument of Perigee (radians)
    nu : float
        True Anomaly (radians)
    mu : float, optional
        Gravitational parameter (km³/s²). Default: Earth
    
    Returns
    -------
    tuple
        (r_vec, v_vec) where:
        - r_vec : Position vector [x, y, z] in km
        - v_vec : Velocity vector [vx, vy, vz] in km/s
    
    Notes
    -----
    Implementation follows Curtis (2013) Algorithm 4.2
    """
    # Perifocal frame position and velocity
    p = a * (1 - e**2)
    
    r_peri = p / (1 + e * math.cos(nu))
    
    r_peri_vec = np.array([
        r_peri * math.cos(nu),
        r_peri * math.sin(nu),
        0
    ])
    
    v_peri_vec = np.array([
        -math.sqrt(mu / p) * math.sin(nu),
        math.sqrt(mu / p) * (e + math.cos(nu)),
        0
    ])
    
    # Rotation matrices
    # First rotation: -omega (argument of perigee)
    cos_w = math.cos(omega)
    sin_w = math.sin(omega)
    R1 = np.array([
        [cos_w, -sin_w, 0],
        [sin_w, cos_w, 0],
        [0, 0, 1]
    ])
    
    # Second rotation: -i (inclination)
    cos_i = math.cos(i)
    sin_i = math.sin(i)
    R2 = np.array([
        [1, 0, 0],
        [0, cos_i, -sin_i],
        [0, sin_i, cos_i]
    ])
    
    # Third rotation: -omega_cap (RAAN)
    cos_wc = math.cos(omega_cap)
    sin_wc = math.sin(omega_cap)
    R3 = np.array([
        [cos_wc, -sin_wc, 0],
        [sin_wc, cos_wc, 0],
        [0, 0, 1]
    ])
    
    # Combined rotation from perifocal to ECI
    R_total = R3 @ R2 @ R1
    
    r_vec = R_total @ r_peri_vec
    v_vec = R_total @ v_peri_vec
    
    return r_vec, v_vec


def mean_anomaly_to_true_anomaly(M, e, tol=1e-10):
    """
    Convert Mean Anomaly to True Anomaly using Kepler's equation.
    
    Parameters
    ----------
    M : float
        Mean anomaly (radians, 0 to 2π)
    e : float
        Eccentricity (0 <= e < 1)
    tol : float
        Convergence tolerance for Newton-Raphson
    
    Returns
    -------
    float
        True anomaly (radians)
    
    Notes
    -----
    Uses Newton-Raphson iteration to solve Kepler's equation: M = E - e*sin(E)
    where E is eccentric anomaly
    """
    # Initial guess for eccentric anomaly
    if e < 0.8:
        E = M
    else:
        E = math.pi
    
    # Newton-Raphson iteration
    for _ in range(50):
        f = E - e * math.sin(E) - M
        f_prime = 1 - e * math.cos(E)
        E_new = E - f / f_prime
        
        if abs(E_new - E) < tol:
            E = E_new
            break
        E = E_new
    
    # Convert eccentric anomaly to true anomaly
    nu = 2 * math.atan2(math.sqrt(1 + e) * math.sin(E / 2),
                        math.sqrt(1 - e) * math.cos(E / 2))
    
    return nu


def true_anomaly_to_mean_anomaly(nu, e):
    """
    Convert True Anomaly to Mean Anomaly.
    
    Parameters
    ----------
    nu : float
        True anomaly (radians)
    e : float
        Eccentricity (0 <= e < 1)
    
    Returns
    -------
    float
        Mean anomaly (radians)
    """
    # Compute eccentric anomaly from true anomaly
    E = 2 * math.atan2(math.sqrt(1 - e) * math.sin(nu / 2),
                       math.sqrt(1 + e) * math.cos(nu / 2))
    
    # Kepler's equation: M = E - e*sin(E)
    M = E - e * math.sin(E)
    
    # Normalize to [0, 2π)
    M = M % (2 * math.pi)
    if M < 0:
        M += 2 * math.pi
    
    return M


def orbital_period(a, mu=GM_EARTH_KM3_S2):
    """
    Calculate orbital period from semi-major axis.
    
    Parameters
    ----------
    a : float
        Semi-major axis (km)
    mu : float, optional
        Gravitational parameter (km³/s²)
    
    Returns
    -------
    float
        Orbital period (seconds)
    
    Notes
    -----
    Uses Kepler's Third Law: T = 2π√(a³/μ)
    """
    return 2 * math.pi * math.sqrt(a**3 / mu)


def orbital_velocity(r, a, mu=GM_EARTH_KM3_S2):
    """
    Calculate orbital velocity at distance r.
    
    Parameters
    ----------
    r : float
        Distance from central body (km)
    a : float
        Semi-major axis (km)
    mu : float, optional
        Gravitational parameter (km³/s²)
    
    Returns
    -------
    float
        Orbital velocity (km/s)
    
    Notes
    -----
    Uses vis-viva equation: v = √(μ(2/r - 1/a))
    """
    return math.sqrt(mu * (2.0 / r - 1.0 / a))


def specific_orbital_energy(a, mu=GM_EARTH_KM3_S2):
    """
    Calculate specific orbital energy (energy per unit mass).
    
    Parameters
    ----------
    a : float
        Semi-major axis (km)
    mu : float, optional
        Gravitational parameter (km³/s²)
    
    Returns
    -------
    float
        Specific orbital energy (km²/s²)
    """
    return -mu / (2.0 * a)


def specific_orbital_angular_momentum(a, e, mu=GM_EARTH_KM3_S2):
    """
    Calculate specific orbital angular momentum.
    
    Parameters
    ----------
    a : float
        Semi-major axis (km)
    e : float
        Eccentricity
    mu : float, optional
        Gravitational parameter (km³/s²)
    
    Returns
    -------
    float
        Specific orbital angular momentum (km²/s)
    """
    return math.sqrt(mu * a * (1 - e**2))
