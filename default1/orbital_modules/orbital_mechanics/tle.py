"""
Two-Line Element (TLE) Set Parser and Handler

Implements NORAD TLE format parsing and propagation using SGP4/SDP4 propagators.

TLE Format Reference:
Line 1: 1 NNNNNU AAAAAAAA BBBBB C DDDDD E FFFFF GGGGG HHHHH III
Line 2: 2 NNNNNU JJJJJ.JJJJJJJJ KKKKK.KKKKKKKK LLLLL.LLLLLLLLL MMM.MMMM NNNNN.NNNNN OOOOO.OOOOOOOO PPPPPPPPP

References:
- NORAD Two-Line Element Set Format. https://celestrak.org/NORAD/documentation/tle-fmt.php
- Vallado, D. A., Crawford, P., Hujsak, R., & Kelso, T. S. (2006).
  "Revisiting Spacetrack Report #3: Rev 1". AIAA Paper 2006-6753.
"""

import re
from datetime import datetime, timedelta
from pyorbcomm import Orbital  # Placeholder; we'll use sgp4 instead
import numpy as np
from .constants import (
    EARTH_RADIUS_KM, GM_EARTH_KM3_S2, SIDEREAL_DAY_SECONDS,
    RAD_TO_DEG, DEG_TO_RAD
)


class TLE:
    """
    Two-Line Element Set handler.
    
    Attributes
    ----------
    satellite_name : str
        Common name of the satellite
    catalog_number : int
        NORAD catalog number
    line1 : str
        TLE line 1
    line2 : str
        TLE line 2
    epoch_year : int
        Epoch year (0-99, interpreted as 1900s/2000s)
    epoch_day : float
        Day of year (1-366.xxxx)
    epoch_datetime : datetime
        Parsed epoch as datetime object
    mean_motion_derivative : float
        First derivative of mean motion (revolutions/day²)
    mean_motion_second_derivative : float
        Second derivative of mean motion (revolutions/day³)
    bstar : float
        Ballistic coefficient
    inclination : float
        Inclination (degrees)
    raan : float
        Right Ascension of Ascending Node (degrees)
    eccentricity : float
        Eccentricity
    argument_of_perigee : float
        Argument of Perigee (degrees)
    mean_anomaly : float
        Mean Anomaly (degrees)
    mean_motion : float
        Mean Motion (revolutions/day)
    """
    
    def __init__(self, line1, line2, satellite_name="UNKNOWN"):
        """
        Initialize TLE from two lines and optional name.
        
        Parameters
        ----------
        line1 : str
            TLE line 1
        line2 : str
            TLE line 2
        satellite_name : str, optional
            Satellite name/common identifier
        """
        self.satellite_name = satellite_name
        self.line1 = line1.strip()
        self.line2 = line2.strip()
        
        # Parse and validate
        self._parse_line1()
        self._parse_line2()
        self._compute_epoch_datetime()
    
    def _parse_line1(self):
        """Parse TLE line 1."""
        # Line format: 1 NNNNNU AAAAAAAA BBBBB C DDDDD E FFFFF GGGGG HHHHH III
        line = self.line1
        
        if not line.startswith('1 '):
            raise ValueError("Line 1 must start with '1 '")
        
        try:
            self.catalog_number = int(line[2:7])
            classification = line[7]
            self.epoch_year = int(line[18:20])
            self.epoch_day = float(line[20:32])
            self.mean_motion_derivative = float(line[33:43]) if line[33:43].strip() else 0.0
            
            # Parse second derivative and ballistic coefficient
            # Line format: GGGGG HHHHH III where GGGGG.HHHHH III is the value
            bstar_str = line[53:61].strip()
            if bstar_str:
                mantissa = float(bstar_str[:-3] or '0') / 1e5
                exponent_str = bstar_str[-3:].strip()
                exponent = int(exponent_str) if exponent_str else 0
                self.bstar = mantissa * (10 ** exponent)
            else:
                self.bstar = 0.0
            
        except (ValueError, IndexError) as e:
            raise ValueError(f"Failed to parse TLE line 1: {e}")
    
    def _parse_line2(self):
        """Parse TLE line 2."""
        line = self.line2
        
        if not line.startswith('2 '):
            raise ValueError("Line 2 must start with '2 '")
        
        try:
            catalog_check = int(line[2:7])
            if catalog_check != self.catalog_number:
                raise ValueError(f"Catalog number mismatch: {catalog_check} vs {self.catalog_number}")
            
            self.inclination = float(line[8:16])
            self.raan = float(line[17:25])
            self.eccentricity = float('0.' + line[26:33])
            self.argument_of_perigee = float(line[34:42])
            self.mean_anomaly = float(line[43:51])
            self.mean_motion = float(line[52:63])
            
        except (ValueError, IndexError) as e:
            raise ValueError(f"Failed to parse TLE line 2: {e}")
    
    def _compute_epoch_datetime(self):
        """Convert TLE epoch to datetime object."""
        # Determine century (assuming 1957 onwards)
        year = 1900 + self.epoch_year if self.epoch_year >= 57 else 2000 + self.epoch_year
        
        # Day of year to datetime
        base_date = datetime(year, 1, 1)
        leap_year = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
        
        day_fraction = self.epoch_day - 1.0
        delta_days = int(day_fraction)
        delta_seconds = (day_fraction - delta_days) * 86400
        
        self.epoch_datetime = base_date + timedelta(days=delta_days, seconds=delta_seconds)
    
    def __str__(self):
        """String representation of TLE."""
        return f"{self.satellite_name}\n{self.line1}\n{self.line2}"
    
    def to_dict(self):
        """Convert TLE to dictionary."""
        return {
            'satellite_name': self.satellite_name,
            'catalog_number': self.catalog_number,
            'epoch_datetime': self.epoch_datetime.isoformat(),
            'inclination_deg': self.inclination,
            'raan_deg': self.raan,
            'eccentricity': self.eccentricity,
            'argument_of_perigee_deg': self.argument_of_perigee,
            'mean_anomaly_deg': self.mean_anomaly,
            'mean_motion_rpm': self.mean_motion,
            'bstar': self.bstar
        }


def parse_tle(name_line, line1, line2):
    """
    Parse TLE from name and two lines.
    
    Parameters
    ----------
    name_line : str
        Satellite name
    line1 : str
        TLE line 1
    line2 : str
        TLE line 2
    
    Returns
    -------
    TLE
        Parsed TLE object
    """
    return TLE(line1, line2, satellite_name=name_line.strip())


def parse_tle_string(tle_string):
    """
    Parse TLE from multi-line string.
    
    Parameters
    ----------
    tle_string : str
        Multi-line TLE (name, line1, line2)
    
    Returns
    -------
    TLE
        Parsed TLE object
    
    Raises
    ------
    ValueError
        If TLE format is invalid
    """
    lines = [line.strip() for line in tle_string.strip().split('\n') if line.strip()]
    
    if len(lines) == 3:
        name, line1, line2 = lines
    elif len(lines) == 2:
        name = "UNKNOWN"
        line1, line2 = lines
    else:
        raise ValueError(f"Expected 2 or 3 lines, got {len(lines)}")
    
    return parse_tle(name, line1, line2)


def tle_from_celestrak_url(url):
    """
    Fetch and parse TLE data from CelesTrak API.
    
    Parameters
    ----------
    url : str
        CelesTrak TLE URL (e.g., 'https://celestrak.org/NORAD/elements/stations.txt')
    
    Returns
    -------
    list
        List of TLE objects
    
    Notes
    -----
    Requires requests library and internet connectivity.
    """
    try:
        import requests
    except ImportError:
        raise ImportError("requests library required for fetching TLE data")
    
    response = requests.get(url)
    response.raise_for_status()
    
    tles = []
    lines = response.text.strip().split('\n')
    
    i = 0
    while i < len(lines):
        if i + 2 < len(lines) and lines[i + 1].startswith('1 ') and lines[i + 2].startswith('2 '):
            # Three-line format with name
            tle = parse_tle(lines[i], lines[i + 1], lines[i + 2])
            tles.append(tle)
            i += 3
        elif i + 1 < len(lines) and lines[i].startswith('1 ') and lines[i + 1].startswith('2 '):
            # Two-line format without name
            tle = TLE(lines[i], lines[i + 1])
            tles.append(tle)
            i += 2
        else:
            i += 1
    
    return tles


def semi_major_axis_from_mean_motion(mean_motion_rpm, mu=GM_EARTH_KM3_S2):
    """
    Calculate semi-major axis from mean motion.
    
    Parameters
    ----------
    mean_motion_rpm : float
        Mean motion (revolutions per day)
    mu : float, optional
        Gravitational parameter (km³/s²)
    
    Returns
    -------
    float
        Semi-major axis (km)
    
    Notes
    -----
    Derived from Kepler's Third Law
    """
    n = mean_motion_rpm * 2 * np.pi / 86400  # Convert to rad/s
    a = (mu / (n**2)) ** (1/3)
    return a


def altitude_from_semi_major_axis(a, ra=EARTH_RADIUS_KM):
    """
    Calculate altitude from semi-major axis (circular orbit approximation).
    
    Parameters
    ----------
    a : float
        Semi-major axis (km)
    ra : float, optional
        Earth radius (km)
    
    Returns
    -------
    float
        Altitude (km)
    """
    return a - ra
