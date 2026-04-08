"""
Live TLE Data Integration

Fetches real-time TLE data from CelesTrak for various satellite catalogs.
Enables live tracking of ISS, GPS constellation, geostationary satellites, etc.

References:
- CelesTrak API: https://celestrak.org/
- NORAD Satellite Database
"""

import requests
from datetime import datetime, timedelta
import json
from .tle import TLE, parse_tle
from .propagators import TwoBodyPropagator, SGP4Wrapper
from .constants import EARTH_RADIUS_KM


class CelesTrakClient:
    """
    CelesTrak API client for fetching live TLE data.
    
    Available catalogs:
    - stations: Space stations (ISS, Tiangong, etc.)
    - active: All active satellites
    - resource: Earth observation satellites
    - sarsat: SARSAT/COSPAS satellites
    - norad-cat-id: Specific satellite by NORAD catalog number
    """
    
    BASE_URL = "https://celestrak.org/NORAD/elements"
    
    CATALOGS = {
        'stations': 'stations.txt',
        'active': 'active.txt',
        'resource': 'resource.txt',
        'sarsat': 'sarsat.txt',
        'weather': 'weather.txt',
        'landsat': 'landsat.txt',
        'goes': 'goes.txt',
        'gps': 'gps-ops.txt',
        'iridium': 'iridium.txt',
        'molniya': 'molniya.txt',
        'other-comm': 'other-comm.txt',
        'other-geo': 'other-geo.txt'
    }
    
    def __init__(self, timeout_seconds=10):
        """
        Initialize CelesTrak client.
        
        Parameters
        ----------
        timeout_seconds : int
            HTTP request timeout
        """
        self.timeout = timeout_seconds
        self.session = requests.Session()
        self.last_update = None
        self.cached_data = {}
    
    def fetch_catalog(self, catalog_name):
        """
        Fetch TLE catalog from CelesTrak.
        
        Parameters
        ----------
        catalog_name : str
            Catalog identifier (stations, active, resource, etc.)
        
        Returns
        -------
        list
            List of TLE objects
        
        Raises
        ------
        requests.RequestException
            If HTTP request fails
        ValueError
            If catalog name invalid
        """
        if catalog_name not in self.CATALOGS:
            raise ValueError(f"Unknown catalog: {catalog_name}. Available: {list(self.CATALOGS.keys())}")
        
        filename = self.CATALOGS[catalog_name]
        url = f"{self.BASE_URL}/{filename}"
        
        try:
            print(f"Fetching {catalog_name} from {url}...")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            tles = self._parse_tle_text(response.text)
            self.cached_data[catalog_name] = {
                'tles': tles,
                'timestamp': datetime.utcnow(),
                'url': url
            }
            self.last_update = datetime.utcnow()
            
            return tles
        
        except requests.RequestException as e:
            print(f"Error fetching from CelesTrak: {e}")
            # Return cached data if available
            if catalog_name in self.cached_data:
                print(f"Using cached data from {self.cached_data[catalog_name]['timestamp']}")
                return self.cached_data[catalog_name]['tles']
            raise
    
    def fetch_satellite_by_name(self, satellite_name):
        """
        Search for satellite by name across active catalog.
        
        Parameters
        ----------
        satellite_name : str
            Satellite name (case-insensitive partial match)
        
        Returns
        -------
        TLE or None
            Matching TLE if found
        """
        try:
            tles = self.fetch_catalog('active')
            search_name = satellite_name.upper()
            
            for tle in tles:
                if search_name in tle.satellite_name.upper():
                    return tle
            
            return None
        except Exception as e:
            print(f"Error searching for satellite: {e}")
            return None
    
    def fetch_satellite_by_catalog_number(self, catalog_number):
        """
        Fetch satellite by NORAD catalog number.
        
        Parameters
        ----------
        catalog_number : int
            NORAD catalog number
        
        Returns
        -------
        TLE or None
            Matching TLE if found
        """
        try:
            tles = self.fetch_catalog('active')
            
            for tle in tles:
                if tle.catalog_number == catalog_number:
                    return tle
            
            return None
        except Exception as e:
            print(f"Error fetching satellite {catalog_number}: {e}")
            return None
    
    def _parse_tle_text(self, text):
        """Parse TLE data from text format."""
        tles = []
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        i = 0
        while i < len(lines):
            if i + 2 < len(lines) and lines[i + 1].startswith('1 ') and lines[i + 2].startswith('2 '):
                try:
                    name = lines[i]
                    line1 = lines[i + 1]
                    line2 = lines[i + 2]
                    tle = TLE(line1, line2, name)
                    tles.append(tle)
                    i += 3
                except Exception as e:
                    print(f"Error parsing TLE: {e}")
                    i += 1
            else:
                i += 1
        
        return tles
    
    def get_cache_age(self, catalog_name):
        """Get age of cached data in seconds."""
        if catalog_name not in self.cached_data:
            return None
        
        age = datetime.utcnow() - self.cached_data[catalog_name]['timestamp']
        return age.total_seconds()


class LiveSatelliteTracker:
    """
    Track live satellite positions using current TLE data.
    """
    
    def __init__(self, tle):
        """
        Initialize tracker with TLE.
        
        Parameters
        ----------
        tle : TLE
            Two-Line Element set
        """
        self.tle = tle
        self.propagator = None
        
        try:
            self.propagator = SGP4Wrapper(tle)
            self.propagation_method = 'SGP4'
        except Exception as e:
            print(f"SGP4 not available: {e}")
            self.propagation_method = 'two-body'
    
    def get_position_now(self):
        """
        Get satellite position at current time.
        
        Returns
        -------
        dict
            Current position and metadata
        """
        now = datetime.utcnow()
        return self.get_position_at_time(now)
    
    def get_position_at_time(self, dt):
        """
        Get satellite position at specific datetime.
        
        Parameters
        ----------
        dt : datetime
            Target datetime (UTC)
        
        Returns
        -------
        dict
            Position, velocity, and orbital information
        """
        try:
            if self.propagator:
                dt_seconds = (dt - self.tle.epoch_datetime).total_seconds()
                result = self.propagator.propagate_dt(dt_seconds)
                
                return {
                    'DateTime': dt.isoformat(),
                    'Position_ECI_km': result['position_km'],
                    'Velocity_ECI_km_s': result['velocity_km_s'],
                    'PropagationMethod': self.propagation_method
                }
        except Exception as e:
            print(f"Error propagating satellite: {e}")
            return None
    
    def get_ground_track_point(self, dt):
        """
        Get ground track point (sub-satellite point).
        
        Parameters
        ----------
        dt : datetime
            Target datetime (UTC)
        
        Returns
        -------
        dict
            Latitude, longitude, altitude
        """
        pos = self.get_position_at_time(dt)
        
        if not pos:
            return None
        
        r_vec = pos['Position_ECI_km']
        r_mag = (r_vec[0]**2 + r_vec[1]**2 + r_vec[2]**2) ** 0.5
        
        import math
        
        # Geocentric latitude
        latitude_rad = math.atan2(r_vec[2], (r_vec[0]**2 + r_vec[1]**2)**0.5)
        latitude_deg = latitude_rad * 180 / math.pi
        
        # Geocentric longitude
        longitude_rad = math.atan2(r_vec[1], r_vec[0])
        
        # Account for Earth rotation
        from .constants import EARTH_ROTATION_RATE_RAD_S
        earth_rotation = EARTH_ROTATION_RATE_RAD_S * (dt - self.tle.epoch_datetime).total_seconds()
        longitude_rad -= earth_rotation
        
        # Normalize longitude
        while longitude_rad > math.pi:
            longitude_rad -= 2 * math.pi
        while longitude_rad < -math.pi:
            longitude_rad += 2 * math.pi
        
        longitude_deg = longitude_rad * 180 / math.pi
        
        return {
            'DateTime': dt.isoformat(),
            'Latitude_deg': latitude_deg,
            'Longitude_deg': longitude_deg,
            'Altitude_km': r_mag - EARTH_RADIUS_KM
        }
    
    def get_ground_track_over_time(self, start_dt, duration_seconds, step_seconds=60):
        """
        Get ground track over a time period.
        
        Parameters
        ----------
        start_dt : datetime
            Start time (UTC)
        duration_seconds : float
            Duration in seconds
        step_seconds : float
            Time step between points
        
        Returns
        -------
        list
            Ground track points
        """
        points = []
        current_time = start_dt
        end_time = start_dt + timedelta(seconds=duration_seconds)
        
        while current_time < end_time:
            point = self.get_ground_track_point(current_time)
            if point:
                points.append(point)
            current_time += timedelta(seconds=step_seconds)
        
        return points


# Common satellite identifiers
COMMON_SATELLITES = {
    'ISS': {
        'name': 'ISS (ZARYA)',
        'catalog_number': 25544,
        'description': 'International Space Station'
    },
    'HUBBLE': {
        'name': 'HST',
        'catalog_number': 20580,
        'description': 'Hubble Space Telescope'
    },
    'LANDSAT-8': {
        'name': 'LANDSAT 8',
        'catalog_number': 39084,
        'description': 'Landsat 8 Earth Observation'
    },
    'NOAA-18': {
        'name': 'NOAA 18',
        'catalog_number': 28654,
        'description': 'NOAA Weather Satellite'
    },
    'GOES-16': {
        'name': 'GOES 16',
        'catalog_number': 41433,
        'description': 'GOES-R (Geostationary)'
    }
}


def get_iss_position_now():
    """
    Convenience function to get ISS position now.
    
    Returns
    -------
    dict
        ISS position data or None on error
    """
    try:
        client = CelesTrakClient()
        iss_tle = client.fetch_satellite_by_catalog_number(25544)
        
        if iss_tle:
            tracker = LiveSatelliteTracker(iss_tle)
            return tracker.get_position_now()
        else:
            print("ISS TLE not found")
            return None
    except Exception as e:
        print(f"Error getting ISS position: {e}")
        return None


def get_live_satellites(catalog_name='stations'):
    """
    Get all satellites from a catalog.
    
    Parameters
    ----------
    catalog_name : str
        Catalog identifier
    
    Returns
    -------
    list
        List of TLE objects
    """
    try:
        client = CelesTrakClient()
        return client.fetch_catalog(catalog_name)
    except Exception as e:
        print(f"Error fetching satellites: {e}")
        return []
