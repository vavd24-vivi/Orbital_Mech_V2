"""
Map Projections for Ground Track Visualization

Implements various map projections suitable for satellite ground track display.
Avoids Mercator projection which distorts polar regions.

References:
- Snyder, J. P. (1987). Map Projections - A Working Manual. USGS Professional Paper 1395.
"""

import numpy as np
import math


class MapProjection:
    """Base class for map projections."""
    
    def project(self, latitude, longitude):
        """
        Project geographic coordinates to 2D map coordinates.
        
        Parameters
        ----------
        latitude : float
            Latitude in degrees (-90 to 90)
        longitude : float
            Longitude in degrees (-180 to 180)
        
        Returns
        -------
        tuple
            (x, y) projected coordinates
        """
        raise NotImplementedError


class SinusoidalProjection(MapProjection):
    """
    Sinusoidal (aka Sanson-Flamsteed) equal-area projection.
    
    Good for: Global coverage, equal area
    Characteristics:
    - Equal area (preserves area ratios)
    - Central meridian is straight line at true scale
    - Other parallels and meridians are curves
    - Minimal distortion near central meridian
    - Used by: NASA MODIS satellite data
    """
    
    def __init__(self, earth_radius=6371, central_meridian=0, width=2000, height=1000):
        """
        Initialize sinusoidal projection.
        
        Parameters
        ----------
        earth_radius : float
            Earth radius in km
        central_meridian : float
            Central meridian in degrees
        width : float
            Map width in pixels
        height : float
            Map height in pixels
        """
        self.radius = earth_radius
        self.central_meridian = central_meridian
        self.width = width
        self.height = height
    
    def project(self, latitude_deg, longitude_deg):
        """Project lat/lon to map coordinates."""
        lat_rad = latitude_deg * math.pi / 180
        lon_rad = longitude_deg * math.pi / 180
        central_rad = self.central_meridian * math.pi / 180
        
        # Sinusoidal projection formulas
        x = self.radius * (lon_rad - central_rad) * math.cos(lat_rad)
        y = self.radius * lat_rad
        
        # Scale to map dimensions
        map_x = (x + self.radius * math.pi) * self.width / (2 * self.radius * math.pi)
        map_y = (self.radius * math.pi / 2 - y) * self.height / (self.radius * math.pi)
        
        return (map_x, map_y)
    
    def unproject(self, x, y):
        """Inverse projection: map coordinates to lat/lon."""
        # Normalize to world coordinates
        world_x = x * (2 * self.radius * math.pi) / self.width - self.radius * math.pi
        world_y = (self.height - y) * (self.radius * math.pi) / self.height - self.radius * math.pi / 2
        
        lat_rad = world_y / self.radius
        lon_rad = world_x / (self.radius * math.cos(lat_rad)) if math.cos(lat_rad) != 0 else 0
        central_rad = self.central_meridian * math.pi / 180
        
        latitude_deg = lat_rad * 180 / math.pi
        longitude_deg = (lon_rad + central_rad) * 180 / math.pi
        
        return (latitude_deg, longitude_deg)


class MollweideProjection(MapProjection):
    """
    Mollweide equal-area projection.
    
    Good for: Whole Earth view, equal area
    Characteristics:
    - Equal area (equal area at all latitudes)
    - Elliptical world outline
    - No distortion at parallels 40°44'N and S
    - Used by: General world maps
    """
    
    def __init__(self, earth_radius=6371, central_meridian=0, width=2000, height=1000):
        """Initialize Mollweide projection."""
        self.radius = earth_radius
        self.central_meridian = central_meridian
        self.width = width
        self.height = height
    
    def project(self, latitude_deg, longitude_deg):
        """Project lat/lon to map coordinates."""
        lat_rad = latitude_deg * math.pi / 180
        lon_rad = longitude_deg * math.pi / 180
        central_rad = self.central_meridian * math.pi / 180
        
        # Mollweide projection parameters
        # Solve for auxiliary angle θ iteratively
        theta = lat_rad
        for _ in range(5):  # Newton-Raphson iterations
            sin_2theta = math.sin(2 * theta)
            cos_2theta = math.cos(2 * theta)
            f = 2 * theta + sin_2theta - math.pi * math.sin(lat_rad)
            f_prime = 2 + 2 * cos_2theta
            theta = theta - f / f_prime
        
        # Mollweide coordinates
        x = (2 * math.sqrt(2) / math.pi) * self.radius * (lon_rad - central_rad) * math.cos(theta)
        y = math.sqrt(2) * self.radius * math.sin(theta)
        
        # Scale to map
        scale_x = self.width / (2.83 * self.radius)
        scale_y = self.height / (1.87 * self.radius)
        
        map_x = x * scale_x + self.width / 2
        map_y = self.height / 2 - y * scale_y
        
        return (map_x, map_y)


class EquirectangularProjection(MapProjection):
    """
    Equirectangular (Plate Carrée) projection.
    
    Good for: Quick display, simple implementation
    Characteristics:
    - Linear latitude and longitude
    - No distortion at equator
    - Severe distortion at poles
    NOT recommended for polar regions
    """
    
    def __init__(self, earth_radius=6371, central_meridian=0, width=2000, height=1000):
        """Initialize equirectangular projection."""
        self.radius = earth_radius
        self.central_meridian = central_meridian
        self.width = width
        self.height = height
    
    def project(self, latitude_deg, longitude_deg):
        """Project lat/lon to map coordinates."""
        lat_rad = latitude_deg * math.pi / 180
        lon_rad = longitude_deg * math.pi / 180
        central_rad = self.central_meridian * math.pi / 180
        
        x = self.radius * (lon_rad - central_rad)
        y = self.radius * lat_rad
        
        # Scale to map
        map_x = (x + self.radius * math.pi) * self.width / (2 * self.radius * math.pi)
        map_y = (self.radius * math.pi / 2 - y) * self.height / (self.radius * math.pi)
        
        return (map_x, map_y)


class LambertAzimuthalProjection(MapProjection):
    """
    Lambert Azimuthal Equal-Area projection with customizable center.
    
    Good for: Polar regions, regional coverage
    Characteristics:
    - Equal area
    - True distance from center point
    - Can be centered on any point
    """
    
    def __init__(self, earth_radius=6371, center_lat=0, center_lon=0, width=2000, height=1000):
        """
        Initialize Lambert Azimuthal projection.
        
        Parameters
        ----------
        center_lat, center_lon : float
            Projection center in degrees
        """
        self.radius = earth_radius
        self.center_lat_rad = center_lat * math.pi / 180
        self.center_lon_rad = center_lon * math.pi / 180
        self.width = width
        self.height = height
    
    def project(self, latitude_deg, longitude_deg):
        """Project lat/lon to map coordinates."""
        lat_rad = latitude_deg * math.pi / 180
        lon_rad = longitude_deg * math.pi / 180
        
        # Distance from center using spherical law of cosines
        cos_c = math.sin(self.center_lat_rad) * math.sin(lat_rad) + \
                math.cos(self.center_lat_rad) * math.cos(lat_rad) * \
                math.cos(lon_rad - self.center_lon_rad)
        
        cos_c = max(-1, min(1, cos_c))  # Clamp to [-1, 1]
        c = math.acos(cos_c)
        
        if c < 1e-10:  # At center
            x = 0
            y = 0
        else:
            sin_c = math.sin(c)
            k = self.radius * c / sin_c
            
            lon_diff = lon_rad - self.center_lon_rad
            x = k * math.cos(lat_rad) * math.sin(lon_diff)
            y = k * (math.cos(self.center_lat_rad) * math.sin(lat_rad) -
                    math.sin(self.center_lat_rad) * math.cos(lat_rad) * math.cos(lon_diff))
        
        # Scale to map
        scale = self.width / (4 * self.radius)
        map_x = self.width / 2 + x * scale
        map_y = self.height / 2 - y * scale
        
        return (map_x, map_y)


def create_ground_track_geojson(ground_track_points, projection='sinusoidal'):
    """
    Create GeoJSON FeatureCollection for ground track.
    
    Parameters
    ----------
    ground_track_points : list
        List of dicts with 'latitude_deg', 'longitude_deg'
    projection : str
        Projection type: 'sinusoidal', 'mollweide', 'equirectangular'
    
    Returns
    -------
    dict
        GeoJSON FeatureCollection
    """
    features = []
    
    for point in ground_track_points:
        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [point['longitude_deg'], point['latitude_deg']]
            },
            'properties': {
                'time': point.get('time', 0),
                'altitude_km': point.get('altitude_km', 0)
            }
        }
        features.append(feature)
    
    return {
        'type': 'FeatureCollection',
        'features': features,
        'properties': {
            'projection': projection,
            'name': 'Satellite Ground Track'
        }
    }


def create_access_window_geojson(ground_track_points, access_windows):
    """
    Create GeoJSON with access windows highlighted.
    
    Parameters
    ----------
    ground_track_points : list
        All ground track points
    access_windows : list
        List of access windows with AOS/LOS times
    
    Returns
    -------
    dict
        GeoJSON with access regions
    """
    features = []
    
    # Add all ground track points
    for point in ground_track_points:
        point_time = point.get('time', 0)
        in_access = False
        
        # Check if this point is in any access window
        for window in access_windows:
            if window['aos_time'] <= point_time <= window['los_time']:
                in_access = True
                break
        
        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [point['longitude_deg'], point['latitude_deg']]
            },
            'properties': {
                'time': point_time,
                'altitude_km': point.get('altitude_km', 0),
                'in_access': in_access
            }
        }
        features.append(feature)
    
    return {
        'type': 'FeatureCollection',
        'features': features,
        'properties': {
            'name': 'Ground Track with Access Windows'
        }
    }
