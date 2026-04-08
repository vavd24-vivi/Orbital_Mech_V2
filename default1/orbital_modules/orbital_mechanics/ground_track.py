"""
Ground Track and Access Calculations

Computes satellite ground track (sub-satellite point) and calculates 
line-of-sight access windows between satellite and ground stations.

References:
- Curtis, H. D. (2013). "Orbital Mechanics for Engineering Students" (3rd ed.).
- Vallado, D. A., Crawford, P., Hujsak, R., & Kelso, T. S. (2006).
  "Revisiting Spacetrack Report #3: Rev 1". AIAA Paper 2006-6753.
"""

import numpy as np
import math
from .constants import (
    EARTH_RADIUS_KM, EARTH_ROTATION_RATE_RAD_S,
    DEG_TO_RAD, RAD_TO_DEG
)
from .conversions import cartesian_to_keplerian


class GroundTrack:
    """
    Calculate satellite ground track over time.
    
    Ground track is the sub-satellite point projected onto Earth's surface
    (point directly below the satellite).
    """
    
    def __init__(self, r_vec_array, times_array, earth_radius=EARTH_RADIUS_KM):
        """
        Initialize ground track calculator.
        
        Parameters
        ----------
        r_vec_array : array_like
            Array of position vectors [N, 3] in ECI frame (km)
        times_array : array_like
            Array of times [N] (seconds since epoch)
        earth_radius : float
            Earth radius (km)
        """
        self.r_vec_array = np.array(r_vec_array)
        self.times_array = np.array(times_array)
        self.earth_radius = earth_radius
        
        if self.r_vec_array.shape[0] != len(self.times_array):
            raise ValueError("r_vec_array and times_array must have same length")
    
    def compute_groundtrack(self):
        """
        Compute ground track (latitude, longitude) for all positions.
        
        Returns
        -------
        list
            List of dicts with 'latitude_deg', 'longitude_deg', 'time'
        """
        groundtrack = []
        
        for i, (r_vec, t) in enumerate(zip(self.r_vec_array, self.times_array)):
            r_mag = np.linalg.norm(r_vec)
            
            # Geocentric latitude
            latitude_rad = math.atan2(r_vec[2], math.sqrt(r_vec[0]**2 + r_vec[1]**2))
            
            # Geocentric longitude (accounting for Earth rotation)
            # Greenwich meridian at epoch: 0 radians
            longitude_ecliptic = math.atan2(r_vec[1], r_vec[0])
            
            # Earth has rotated since epoch
            earth_rotation = EARTH_ROTATION_RATE_RAD_S * t
            longitude_rad = longitude_ecliptic - earth_rotation
            
            # Normalize to [-π, π]
            while longitude_rad > math.pi:
                longitude_rad -= 2 * math.pi
            while longitude_rad < -math.pi:
                longitude_rad += 2 * math.pi
            
            groundtrack.append({
                'latitude_deg': latitude_rad * RAD_TO_DEG,
                'longitude_deg': longitude_rad * RAD_TO_DEG,
                'time': t,
                'altitude_km': r_mag - self.earth_radius
            })
        
        return groundtrack


class AccessCalculator:
    """
    Calculate line-of-sight access between satellite and ground station.
    
    Access window: time period when satellite is visible from ground station.
    AOS: Acquisition of Signal (satellite comes into view)
    LOS: Loss of Signal (satellite goes out of view)
    """
    
    def __init__(self, ground_lat, ground_lon, min_elevation_deg=0.0, 
                 earth_radius=EARTH_RADIUS_KM):
        """
        Initialize access calculator with ground station.
        
        Parameters
        ----------
        ground_lat : float
            Ground station latitude (degrees)
        ground_lon : float
            Ground station longitude (degrees)
        min_elevation_deg : float
            Minimum elevation angle for access (degrees, 0-90)
        earth_radius : float
            Earth radius (km)
        """
        self.ground_lat_rad = ground_lat * DEG_TO_RAD
        self.ground_lon_rad = ground_lon * DEG_TO_RAD
        self.min_elevation_rad = min_elevation_deg * DEG_TO_RAD
        self.earth_radius = earth_radius
        
        # Convert ground station to ECI coordinates (simplified, assumes mean rotation)
        self.ground_station_ecef = self._lat_lon_to_ecef(ground_lat, ground_lon)
    
    def _lat_lon_to_ecef(self, latitude_deg, longitude_deg):
        """Convert lat/lon to ECEF coordinates."""
        lat_rad = latitude_deg * DEG_TO_RAD
        lon_rad = longitude_deg * DEG_TO_RAD
        
        x = self.earth_radius * math.cos(lat_rad) * math.cos(lon_rad)
        y = self.earth_radius * math.cos(lat_rad) * math.sin(lon_rad)
        z = self.earth_radius * math.sin(lat_rad)
        
        return np.array([x, y, z])
    
    def can_access(self, sat_position_eci, time=0):
        """
        Check if satellite is visible from ground station at given time.
        
        Parameters
        ----------
        sat_position_eci : array_like
            Satellite position in ECI frame (km)
        time : float, optional
            Time since epoch (seconds)
        
        Returns
        -------
        dict
            Access information dictionary
        
        Notes
        -----
        Includes:
        - 'visible': True/False
        - 'elevation_deg': Elevation angle above horizon
        - 'azimuth_deg': Azimuth from ground station
        - 'slant_range_km': Distance to satellite
        """
        sat_pos = np.array(sat_position_eci)
        
        # Account for Earth rotation
        earth_rotation = EARTH_ROTATION_RATE_RAD_S * time
        
        # Rotate ground station to current epoch
        cos_rot = math.cos(earth_rotation)
        sin_rot = math.sin(earth_rotation)
        rotation_matrix = np.array([
            [cos_rot, -sin_rot, 0],
            [sin_rot, cos_rot, 0],
            [0, 0, 1]
        ])
        
        ground_pos = rotation_matrix @ self.ground_station_ecef
        
        # Vector from ground station to satellite
        line_of_sight = sat_pos - ground_pos
        los_distance = np.linalg.norm(line_of_sight)
        
        # Check if line of sight intersects Earth
        # Closest approach to Earth center
        a = np.linalg.norm(ground_pos)
        b = 2 * np.dot(ground_pos, line_of_sight)
        c = los_distance**2 - self.earth_radius**2
        
        # Line of sight clipped to segment [0, 1]
        t_closest = -b / (2 * los_distance**2) if los_distance > 0 else 0
        t_closest = max(0, min(1, t_closest))
        
        closest_point = ground_pos + t_closest * line_of_sight
        closest_distance = np.linalg.norm(closest_point)
        
        line_blocked = closest_distance < self.earth_radius
        
        # Calculate elevation angle
        zenith_angle = math.acos(np.clip(np.dot(-ground_pos, line_of_sight) / 
                                        (np.linalg.norm(ground_pos) * los_distance),
                                        -1, 1))
        elevation = math.pi / 2 - zenith_angle
        
        # Calculate azimuth (simplified)
        azimuth = math.atan2(sat_pos[1] - ground_pos[1],
                            sat_pos[0] - ground_pos[0])
        if azimuth < 0:
            azimuth += 2 * math.pi
        
        visible = (not line_blocked) and (elevation >= self.min_elevation_rad)
        
        return {
            'visible': visible,
            'elevation_deg': elevation * RAD_TO_DEG,
            'azimuth_deg': azimuth * RAD_TO_DEG,
            'slant_range_km': los_distance,
            'time': time
        }
    
    def compute_access_windows(self, r_vec_array, times_array):
        """
        Compute access windows over time.
        
        Parameters
        ----------
        r_vec_array : array_like
            Array of satellite positions (N, 3) in ECI
        times_array : array_like
            Array of times (N,) in seconds
        
        Returns
        -------
        list
            List of access windows with AOS/LOS times
        """
        access_data = []
        for r_vec, t in zip(r_vec_array, times_array):
            result = self.can_access(r_vec, t)
            access_data.append(result)
        
        # Find transitions from not visible to visible (AOS) and vice versa (LOS)
        windows = []
        in_view = False
        aos_time = None
        
        for i, data in enumerate(access_data):
            if data['visible'] and not in_view:
                # Acquisition of signal
                aos_time = data['time']
                in_view = True
            elif not data['visible'] and in_view:
                # Loss of signal
                if aos_time is not None:
                    windows.append({
                        'aos_time': aos_time,
                        'los_time': data['time'],
                        'duration': data['time'] - aos_time,
                        'max_elevation_deg': max([d['elevation_deg'] for d in access_data 
                                                 if d['time'] >= aos_time and 
                                                 d['time'] <= data['time']]),
                        'max_slant_range_km': max([d['slant_range_km'] for d in access_data
                                                  if d['time'] >= aos_time and
                                                  d['time'] <= data['time']])
                    })
                in_view = False
        
        # Handle open window at end
        if in_view and aos_time is not None:
            last_time = times_array[-1]
            windows.append({
                'aos_time': aos_time,
                'los_time': last_time,
                'duration': last_time - aos_time,
                'max_elevation_deg': max([d['elevation_deg'] for d in access_data 
                                         if d['time'] >= aos_time]),
                'max_slant_range_km': max([d['slant_range_km'] for d in access_data
                                          if d['time'] >= aos_time])
            })
        
        return windows


def compute_horizon_distance(altitude_km, earth_radius=EARTH_RADIUS_KM):
    """
    Compute horizon distance for satellite at given altitude.
    
    Parameters
    ----------
    altitude_km : float
        Satellite altitude (km)
    earth_radius : float
        Earth radius (km)
    
    Returns
    -------
    float
        Horizon distance (km)
    
    Notes
    -----
    For ground coverage calculations. Uses simple geometric approximation.
    """
    r = earth_radius + altitude_km
    
    # Distance from Earth center to satellite
    # Tangent line to Earth's surface
    cos_angle = earth_radius / r
    angle = math.acos(np.clip(cos_angle, -1, 1))
    
    # Arc length on Earth's surface
    horizon_distance = earth_radius * angle
    
    return horizon_distance


def compute_sun_angle(sat_position_eci, sun_position_eci):
    """
    Compute angle between satellite and sun direction from Earth.
    
    Parameters
    ----------
    sat_position_eci : array_like
        Satellite position in ECI (km)
    sun_position_eci : array_like
        Sun position in ECI (km)
    
    Returns
    -------
    float
        Sun angle (radians, 0 to π)
    
    Notes
    -----
    Used to determine if satellite is in sunlight (eclipse calculations).
    """
    sat_vec = np.array(sat_position_eci)
    sun_vec = np.array(sun_position_eci)
    
    # Normalize sun direction
    sun_direction = sun_vec / np.linalg.norm(sun_vec)
    sat_direction = sat_vec / np.linalg.norm(sat_vec)
    
    angle = math.acos(np.clip(np.dot(sat_direction, sun_direction), -1, 1))
    
    return angle
