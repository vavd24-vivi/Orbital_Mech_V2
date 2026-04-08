"""
Real-time Animation and Visualization Support

Provides data structures and algorithms for real-time satellite orbit animation.
"""

import numpy as np
from datetime import datetime, timedelta
from .propagators import TwoBodyPropagator, J2Propagator
from .conversions import cartesian_to_keplerian, keplerian_to_cartesian
from .constants import GM_EARTH_KM3_S2, EARTH_RADIUS_KM


class OrbitAnimationGenerator:
    """
    Generate animation frames for satellite orbit propagation.
    """
    
    def __init__(self, initial_state, num_orbits=1, frames_per_orbit=360, 
                 propagator_type='two-body'):
        """
        Initialize animation generator.
        
        Parameters
        ----------
        initial_state : dict
            Either {'position': [...], 'velocity': [...]} or Keplerian elements
        num_orbits : float
            Number of orbits to animate
        frames_per_orbit : int
            Animation frames per orbit
        propagator_type : str
            'two-body' or 'j2'
        """
        self.num_orbits = num_orbits
        self.frames_per_orbit = frames_per_orbit
        self.total_frames = int(num_orbits * frames_per_orbit)
        self.propagator_type = propagator_type
        
        # Determine orbit period
        if 'position' in initial_state:
            # State vector format
            r_vec = initial_state['position']
            v_vec = initial_state['velocity']
            kep = cartesian_to_keplerian(r_vec, v_vec)
            a = kep['a']
        else:
            # Keplerian format
            a = initial_state.get('a', initial_state.get('semi_major_axis_km', 7000))
        
        # Calculate period
        period = 2 * np.pi * np.sqrt(a**3 / GM_EARTH_KM3_S2)
        self.dt = period / frames_per_orbit
        self.total_time = period * num_orbits
        
        # Setup propagator
        if 'position' in initial_state:
            self.propagator = TwoBodyPropagator(
                initial_state['position'],
                initial_state['velocity']
            )
        else:
            kep = {
                'a': initial_state.get('a', 7000),
                'e': initial_state.get('e', 0),
                'i': initial_state.get('i', 0),
                'omega_cap': initial_state.get('omega_cap', 0),
                'omega': initial_state.get('omega', 0),
                'nu': initial_state.get('nu', 0)
            }
            r, v = keplerian_to_cartesian(kep['a'], kep['e'], kep['i'],
                                         kep['omega_cap'], kep['omega'], kep['nu'])
            self.propagator = TwoBodyPropagator(r, v)
    
    def generate_frames(self):
        """
        Generate all animation frames.
        
        Yields
        ------
        dict
            Frame data with position, velocity, time, etc.
        """
        current_time = 0
        
        for frame_num in range(self.total_frames):
            r, v = self.propagator.propagate(current_time)
            
            kep = cartesian_to_keplerian(r, v)
            r_mag = np.linalg.norm(r)
            v_mag = np.linalg.norm(v)
            altitude = r_mag - EARTH_RADIUS_KM
            
            yield {
                'frame': frame_num,
                'time_seconds': current_time,
                'position_eci': r.tolist(),
                'velocity_eci': v.tolist(),
                'position_magnitude_km': float(r_mag),
                'velocity_magnitude_km_s': float(v_mag),
                'altitude_km': float(altitude),
                'semi_major_axis_km': float(kep['a']),
                'eccentricity': float(kep['e']),
                'inclination_deg': float(kep['i'] * 180 / np.pi),
                'true_anomaly_deg': float(kep['nu'] * 180 / np.pi)
            }
            
            current_time += self.dt


class GroundTrackAnimationGenerator:
    """
    Generate ground track animation frames.
    """
    
    def __init__(self, satellite_position_func, start_datetime, duration_seconds, 
                 step_seconds=10):
        """
        Initialize ground track animation.
        
        Parameters
        ----------
        satellite_position_func : callable
            Function that returns position ECI at given datetime
        start_datetime : datetime
            Start time
        duration_seconds : float
            Duration to animate
        step_seconds : float
            Time step between frames
        """
        self.position_func = satellite_position_func
        self.start_time = start_datetime
        self.duration = duration_seconds
        self.step = step_seconds
        self.num_frames = int(duration_seconds / step_seconds)
    
    def generate_frames(self):
        """
        Generate ground track frames.
        
        Yields
        ------
        dict
            Ground track point with lat/lon/altitude
        """
        from .constants import EARTH_ROTATION_RATE_RAD_S
        import math
        
        current_time = self.start_time
        
        for frame_num in range(self.num_frames):
            try:
                r_vec = self.position_func(current_time)
                
                if r_vec is None:
                    current_time += timedelta(seconds=self.step)
                    continue
                
                r_mag = np.linalg.norm(r_vec)
                
                # Geocentric latitude
                latitude_rad = math.atan2(r_vec[2], 
                                        (r_vec[0]**2 + r_vec[1]**2)**0.5)
                latitude_deg = latitude_rad * 180 / math.pi
                
                # Geocentric longitude
                longitude_rad = math.atan2(r_vec[1], r_vec[0])
                
                # Account for Earth rotation
                earth_rotation = EARTH_ROTATION_RATE_RAD_S * \
                               (current_time - self.start_time).total_seconds()
                longitude_rad -= earth_rotation
                
                # Normalize longitude
                while longitude_rad > math.pi:
                    longitude_rad -= 2 * math.pi
                while longitude_rad < -math.pi:
                    longitude_rad += 2 * math.pi
                
                longitude_deg = longitude_rad * 180 / math.pi
                
                yield {
                    'frame': frame_num,
                    'time': current_time.isoformat(),
                    'latitude_deg': float(latitude_deg),
                    'longitude_deg': float(longitude_deg),
                    'altitude_km': float(r_mag - EARTH_RADIUS_KM)
                }
            
            except Exception as e:
                print(f"Error generating frame {frame_num}: {e}")
            
            current_time += timedelta(seconds=self.step)


class ComparativeAnimationGenerator:
    """
    Generate comparative animations between different propagators.
    """
    
    def __init__(self, initial_state, num_orbits=1, frames_per_orbit=360):
        """Initialize comparative animation."""
        self.initial_state = initial_state
        self.num_orbits = num_orbits
        self.frames_per_orbit = frames_per_orbit
        
        # Setup both propagators
        if 'position' in initial_state:
            r_vec = initial_state['position']
            v_vec = initial_state['velocity']
            self.propagator_2body = TwoBodyPropagator(r_vec, v_vec)
            
            kep = cartesian_to_keplerian(r_vec, v_vec)
            self.propagator_j2 = J2Propagator(
                kep['a'], kep['e'], kep['i'],
                kep['omega_cap'], kep['omega'], kep['nu']
            )
        
        # Calculate period
        a = self.propagator_2body.kep['a']
        period = 2 * np.pi * np.sqrt(a**3 / GM_EARTH_KM3_S2)
        self.dt = period / frames_per_orbit
        self.total_frames = int(num_orbits * frames_per_orbit)
    
    def generate_frames(self):
        """
        Generate comparative frames.
        
        Yields
        ------
        dict
            Frame data from both propagators
        """
        current_time = 0
        
        for frame_num in range(self.total_frames):
            # Two-body propagation
            r_2body, v_2body = self.propagator_2body.propagate(current_time)
            kep_2body = cartesian_to_keplerian(r_2body, v_2body)
            
            # J2 propagation
            kep_j2 = self.propagator_j2.propagate(current_time)
            r_j2, v_j2 = keplerian_to_cartesian(
                kep_j2['a'], kep_j2['e'], kep_j2['i'],
                kep_j2['omega_cap'], kep_j2['omega'], kep_j2['nu']
            )
            
            # Position difference
            pos_diff = np.linalg.norm(r_2body - r_j2)
            
            yield {
                'frame': frame_num,
                'time_seconds': current_time,
                'two_body': {
                    'position': r_2body.tolist(),
                    'true_anomaly_deg': float(kep_2body['nu'] * 180 / np.pi),
                    'raan_deg': float(kep_2body['omega_cap'] * 180 / np.pi)
                },
                'j2_perturbed': {
                    'position': r_j2.tolist(),
                    'true_anomaly_deg': float(kep_j2['nu'] * 180 / np.pi),
                    'raan_deg': float(kep_j2['omega_cap'] * 180 / np.pi)
                },
                'position_divergence_km': float(pos_diff),
                'raan_difference_deg': float(
                    (kep_j2['omega_cap'] - kep_2body['omega_cap']) * 180 / np.pi
                )
            }
            
            current_time += self.dt


def create_orbit_trail_geometry(positions, color='red'):
    """
    Create orbit trail geometry for visualization.
    
    Parameters
    ----------
    positions : list
        List of position vectors [x, y, z]
    color : str
        Trail color name
    
    Returns
    -------
    dict
        Geometry suitable for 3D visualization
    """
    return {
        'type': 'line',
        'coordinates': positions,
        'color': color,
        'width': 2
    }
