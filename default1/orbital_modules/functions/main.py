"""
Firebase Cloud Functions for Orbital Dynamics
Replaces Flask backend with serverless architecture

This runs on Google Cloud Functions with Python 3.12 runtime.
All orbital mechanics calculations remain identical to the Flask backend.
"""

import functions_framework
from flask import Request, jsonify
import numpy as np
import traceback
from datetime import datetime, timedelta
import json
import sys
import os

# Add orbital_modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'orbital_modules'))

# Import orbital mechanics modules
from tle import TLE, parse_tle_string, semi_major_axis_from_mean_motion
from conversions import (
    cartesian_to_keplerian, keplerian_to_cartesian,
    mean_anomaly_to_true_anomaly, orbital_period, orbital_velocity
)
from propagators import (
    TwoBodyPropagator, J2Propagator, compare_propagators
)
from maneuvers import (
    HohmannTransfer, BiellipticTransfer, PlaneChange
)
from ground_track import (
    GroundTrack, AccessCalculator, compute_horizon_distance
)
from orbit_catalog import (
    get_orbit_info, list_all_orbits, calculate_orbital_period
)
from constants import (
    EARTH_RADIUS_KM, GM_EARTH_KM3_S2, DEG_TO_RAD, RAD_TO_DEG
)
from advanced_perturbations import (
    AdvancedPerturbationPropagator, LaunchWindowOptimizer
)
from projections import (
    SinusoidalProjection, MollweideProjection,
    EquirectangularProjection, LambertAzimuthalProjection
)


def cors_headers():
    """Return CORS headers for Cross-Origin requests"""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    }


def handle_error(error):
    """Handle all errors and return JSON response."""
    print(f"Error: {error}")
    traceback.print_exc()
    return jsonify({
        'error': str(error),
        'type': type(error).__name__
    }), 400


# ============================================================================
# MAIN ROUTER FUNCTION
# ============================================================================

@functions_framework.http
def orbitalDynamicsAPI(request: Request):
    """
    Main HTTP router for all orbital dynamics endpoints.
    Routes requests to appropriate handlers based on path.
    
    Supports:
    - /api/tle/* - TLE parsing and analysis
    - /api/conversions/* - State vector ↔ Keplerian conversions
    - /api/maneuvers/* - Orbital maneuver calculations
    - /api/propagation/* - Orbit propagation
    - /api/orbits/* - Orbit catalog queries
    - /api/ground-track/* - Ground track and access analysis
    """
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return ('', 204, cors_headers())
    
    try:
        # Extract path and method
        path = request.path
        method = request.method
        
        # Route to appropriate handler
        if '/tle/' in path:
            if path.endswith('/parse'):
                return parse_tle_endpoint(request)
            elif path.endswith('/info'):
                return tle_info_endpoint(request)
        
        elif '/conversions/' in path:
            if path.endswith('/keplerian-to-state'):
                return keplerian_to_state_endpoint(request)
            elif path.endswith('/state-to-keplerian'):
                return state_to_keplerian_endpoint(request)
        
        elif '/maneuvers/' in path:
            if path.endswith('/hohmann'):
                return hohmann_transfer_endpoint(request)
            elif path.endswith('/bielliptic'):
                return bielliptic_transfer_endpoint(request)
            elif path.endswith('/plane-change'):
                return plane_change_endpoint(request)
        
        elif '/propagation/' in path:
            if path.endswith('/two-body'):
                return two_body_propagation_endpoint(request)
            elif path.endswith('/j2-perturbed'):
                return j2_propagation_endpoint(request)
            elif path.endswith('/compare'):
                return compare_propagators_endpoint(request)
        
        elif '/orbits/' in path:
            if path.endswith('/list'):
                return list_orbits_endpoint(request)
            elif path.endswith('/info'):
                return orbit_info_endpoint(request)
        
        elif '/ground-track/' in path:
            if path.endswith('/calculate'):
                return ground_track_endpoint(request)
            elif path.endswith('/access'):
                return access_window_endpoint(request)
        
        return (
            jsonify({
                'error': f'Endpoint not found: {path}',
                'available_endpoints': [
                    '/api/tle/parse',
                    '/api/tle/info',
                    '/api/conversions/keplerian-to-state',
                    '/api/conversions/state-to-keplerian',
                    '/api/maneuvers/hohmann',
                    '/api/maneuvers/bielliptic',
                    '/api/maneuvers/plane-change',
                    '/api/propagation/two-body',
                    '/api/propagation/j2-perturbed',
                    '/api/propagation/compare',
                    '/api/orbits/list',
                    '/api/orbits/info',
                    '/api/ground-track/calculate',
                    '/api/ground-track/access'
                ]
            }),
            404,
            cors_headers()
        )
    
    except Exception as e:
        return (handle_error(e)[0], handle_error(e)[1] or 400, cors_headers())


# ============================================================================
# TLE ENDPOINTS
# ============================================================================

def parse_tle_endpoint(request: Request):
    """Parse TLE from input lines"""
    data = request.get_json()
    try:
        tle = TLE(data['line1'], data['line2'], data.get('name', 'UNKNOWN'))
        response = jsonify(tle.to_dict())
        response.headers.update(cors_headers())
        return response
    except Exception as e:
        return (jsonify({'error': str(e)}), 400, cors_headers())


def tle_info_endpoint(request: Request):
    """Get calculated info from TLE"""
    data = request.get_json()
    try:
        tle = TLE(data['line1'], data['line2'], data.get('name', 'UNKNOWN'))
        a = semi_major_axis_from_mean_motion(tle.mean_motion)
        period = orbital_period(a)
        
        response = jsonify({
            'name': tle.name,
            'semi_major_axis_km': a,
            'orbital_period_minutes': period,
            'mean_motion_rev_per_day': tle.mean_motion,
            'epoch': str(tle.epoch),
            'inclination_deg': tle.inclination,
            'eccentricity': tle.eccentricity
        })
        response.headers.update(cors_headers())
        return response
    except Exception as e:
        return (jsonify({'error': str(e)}), 400, cors_headers())


# ============================================================================
# CONVERSION ENDPOINTS
# ============================================================================

def keplerian_to_state_endpoint(request: Request):
    """Convert Keplerian elements to Cartesian state vector"""
    data = request.get_json()
    try:
        state = keplerian_to_cartesian(
            semi_major_axis_km=data['semi_major_axis_km'],
            eccentricity=data['eccentricity'],
            inclination_deg=data['inclination_deg'],
            raan_deg=data['raan_deg'],
            argument_of_perigee_deg=data['argument_of_perigee_deg'],
            true_anomaly_deg=data['true_anomaly_deg']
        )
        
        response = jsonify({
            'position': [float(x) for x in state[0]],
            'velocity': [float(x) for x in state[1]],
            'position_magnitude_km': float(np.linalg.norm(state[0])),
            'velocity_magnitude_km_s': float(np.linalg.norm(state[1]))
        })
        response.headers.update(cors_headers())
        return response
    except Exception as e:
        return (jsonify({'error': str(e)}), 400, cors_headers())


def state_to_keplerian_endpoint(request: Request):
    """Convert state vector to Keplerian elements"""
    data = request.get_json()
    try:
        position = np.array(data['position'])
        velocity = np.array(data['velocity'])
        
        keplerian = cartesian_to_keplerian(position, velocity)
        
        response = jsonify({
            'semi_major_axis_km': float(keplerian[0]),
            'eccentricity': float(keplerian[1]),
            'inclination_deg': float(keplerian[2]),
            'raan_deg': float(keplerian[3]),
            'argument_of_perigee_deg': float(keplerian[4]),
            'true_anomaly_deg': float(keplerian[5]),
            'orbital_period_minutes': float(orbital_period(keplerian[0]))
        })
        response.headers.update(cors_headers())
        return response
    except Exception as e:
        return (jsonify({'error': str(e)}), 400, cors_headers())


# ============================================================================
# MANEUVER ENDPOINTS
# ============================================================================

def hohmann_transfer_endpoint(request: Request):
    """Calculate Hohmann transfer between two circular orbits"""
    data = request.get_json()
    try:
        transfer = HohmannTransfer(data['r1_km'], data['r2_km'])
        
        response = jsonify({
            'delta_v_1_km_s': float(transfer.delta_v_1),
            'delta_v_2_km_s': float(transfer.delta_v_2),
            'total_delta_v_km_s': float(transfer.total_delta_v),
            'transfer_time_minutes': float(transfer.transfer_time),
            'semi_major_axis_transfer': float(transfer.a_transfer),
            'efficiency': 'Hohmann transfer (minimum energy for coplanar circular orbits)'
        })
        response.headers.update(cors_headers())
        return response
    except Exception as e:
        return (jsonify({'error': str(e)}), 400, cors_headers())


def bielliptic_transfer_endpoint(request: Request):
    """Calculate bi-elliptic transfer"""
    data = request.get_json()
    try:
        transfer = BiellipticTransfer(
            data['r1_km'],
            data['r2_km'],
            data.get('r_intermediate_km', data['r2_km'] * 1.5)
        )
        
        response = jsonify({
            'delta_v_1_km_s': float(transfer.delta_v_1),
            'delta_v_2_km_s': float(transfer.delta_v_2),
            'delta_v_3_km_s': float(transfer.delta_v_3),
            'total_delta_v_km_s': float(transfer.total_delta_v),
            'transfer_time_minutes': float(transfer.transfer_time),
            'more_efficient_than_hohmann': transfer.more_efficient_than_hohmann
        })
        response.headers.update(cors_headers())
        return response
    except Exception as e:
        return (jsonify({'error': str(e)}), 400, cors_headers())


def plane_change_endpoint(request: Request):
    """Calculate plane change maneuver"""
    data = request.get_json()
    try:
        plane_change = PlaneChange(
            data['orbital_radius_km'],
            data['inclination_change_deg'],
            data.get('velocity_km_s', None)
        )
        
        response = jsonify({
            'delta_v_km_s': float(plane_change.delta_v),
            'inclination_change_deg': float(data['inclination_change_deg']),
            'orbital_radius_km': float(data['orbital_radius_km'])
        })
        response.headers.update(cors_headers())
        return response
    except Exception as e:
        return (jsonify({'error': str(e)}), 400, cors_headers())


# ============================================================================
# PROPAGATION ENDPOINTS
# ============================================================================

def two_body_propagation_endpoint(request: Request):
    """Propagate orbit using two-body Keplerian model"""
    data = request.get_json()
    try:
        propagator = TwoBodyPropagator(
            semi_major_axis_km=data['semi_major_axis_km'],
            eccentricity=data['eccentricity'],
            inclination_deg=data['inclination_deg'],
            raan_deg=data['raan_deg'],
            argument_of_perigee_deg=data['argument_of_perigee_deg'],
            true_anomaly_deg=data['true_anomaly_deg']
        )
        
        times = np.linspace(0, data.get('duration_hours', 24), data.get('num_points', 100))
        positions = []
        
        for t in times:
            pos, vel = propagator.propagate(t * 3600)  # Convert hours to seconds
            positions.append([float(x) for x in pos])
        
        response = jsonify({
            'times_hours': [float(t) for t in times],
            'positions_km': positions,
            'propagator': 'TwoBodyPropagator',
            'model': 'Keplerian (spherical central body)'
        })
        response.headers.update(cors_headers())
        return response
    except Exception as e:
        return (jsonify({'error': str(e)}), 400, cors_headers())


def j2_propagation_endpoint(request: Request):
    """Propagate orbit using J2-perturbed model"""
    data = request.get_json()
    try:
        propagator = J2Propagator(
            semi_major_axis_km=data['semi_major_axis_km'],
            eccentricity=data['eccentricity'],
            inclination_deg=data['inclination_deg'],
            raan_deg=data['raan_deg'],
            argument_of_perigee_deg=data['argument_of_perigee_deg'],
            true_anomaly_deg=data['true_anomaly_deg']
        )
        
        times = np.linspace(0, data.get('duration_hours', 24), data.get('num_points', 100))
        positions = []
        raan_values = []
        aop_values = []
        
        for t in times:
            pos, vel = propagator.propagate(t * 3600)
            positions.append([float(x) for x in pos])
            raan_values.append(float(propagator.raan))
            aop_values.append(float(propagator.aop))
        
        response = jsonify({
            'times_hours': [float(t) for t in times],
            'positions_km': positions,
            'raan_progression_deg': raan_values,
            'aop_progression_deg': aop_values,
            'propagator': 'J2Propagator',
            'model': 'J2 oblateness perturbations'
        })
        response.headers.update(cors_headers())
        return response
    except Exception as e:
        return (jsonify({'error': str(e)}), 400, cors_headers())


def compare_propagators_endpoint(request: Request):
    """Compare TwoBody vs J2 propagation"""
    data = request.get_json()
    try:
        prop1 = TwoBodyPropagator(
            data['semi_major_axis_km'], data['eccentricity'],
            data['inclination_deg'], data['raan_deg'],
            data['argument_of_perigee_deg'], data['true_anomaly_deg']
        )
        prop2 = J2Propagator(
            data['semi_major_axis_km'], data['eccentricity'],
            data['inclination_deg'], data['raan_deg'],
            data['argument_of_perigee_deg'], data['true_anomaly_deg']
        )
        
        times = np.linspace(0, data.get('duration_hours', 24), data.get('num_points', 50))
        
        two_body_pos = []
        j2_pos = []
        position_errors = []
        
        for t in times:
            pos1, _ = prop1.propagate(t * 3600)
            pos2, _ = prop2.propagate(t * 3600)
            two_body_pos.append([float(x) for x in pos1])
            j2_pos.append([float(x) for x in pos2])
            error = np.linalg.norm(pos1 - pos2)
            position_errors.append(float(error))
        
        response = jsonify({
            'times_hours': [float(t) for t in times],
            'two_body_positions': two_body_pos,
            'j2_positions': j2_pos,
            'position_errors_km': position_errors,
            'max_error_km': max(position_errors),
            'note': 'J2 model includes Earth oblateness effects'
        })
        response.headers.update(cors_headers())
        return response
    except Exception as e:
        return (jsonify({'error': str(e)}), 400, cors_headers())


# ============================================================================
# ORBIT CATALOG ENDPOINTS
# ============================================================================

def list_orbits_endpoint(request: Request):
    """List all available orbit types"""
    try:
        orbits = list_all_orbits()
        response = jsonify({
            'orbits': orbits,
            'count': len(orbits)
        })
        response.headers.update(cors_headers())
        return response
    except Exception as e:
        return (jsonify({'error': str(e)}), 400, cors_headers())


def orbit_info_endpoint(request: Request):
    """Get information about specific orbit type"""
    data = request.get_json()
    try:
        orbit_info = get_orbit_info(data['orbit_type'])
        response = jsonify(orbit_info)
        response.headers.update(cors_headers())
        return response
    except Exception as e:
        return (jsonify({'error': str(e)}), 400, cors_headers())


# ============================================================================
# GROUND TRACK & ACCESS ENDPOINTS
# ============================================================================

def ground_track_endpoint(request: Request):
    """Calculate ground track for satellite"""
    data = request.get_json()
    try:
        gt = GroundTrack(
            semi_major_axis_km=data['semi_major_axis_km'],
            eccentricity=data['eccentricity'],
            inclination_deg=data['inclination_deg'],
            raan_deg=data['raan_deg'],
            argument_of_perigee_deg=data['argument_of_perigee_deg'],
            true_anomaly_deg=data['true_anomaly_deg']
        )
        
        ground_track_data = gt.calculate_ground_track(data.get('num_points', 100))
        
        response = jsonify({
            'longitudes': [float(x[0]) for x in ground_track_data],
            'latitudes': [float(x[1]) for x in ground_track_data],
            'satellite_name': data.get('satellite_name', 'Unknown')
        })
        response.headers.update(cors_headers())
        return response
    except Exception as e:
        return (jsonify({'error': str(e)}), 400, cors_headers())


def access_window_endpoint(request: Request):
    """Calculate access windows from ground station"""
    data = request.get_json()
    try:
        calc = AccessCalculator(
            semi_major_axis_km=data['semi_major_axis_km'],
            eccentricity=data['eccentricity'],
            inclination_deg=data['inclination_deg'],
            raan_deg=data['raan_deg'],
            argument_of_perigee_deg=data['argument_of_perigee_deg'],
            true_anomaly_deg=data['true_anomaly_deg'],
            ground_station_lat=data['ground_station_lat'],
            ground_station_lon=data['ground_station_lon'],
            elevation_mask_deg=data.get('elevation_mask_deg', 0)
        )
        
        windows = calc.calculate_access_windows(data.get('num_orbits', 5))
        
        response = jsonify({
            'access_windows': windows,
            'ground_station': {
                'latitude': data['ground_station_lat'],
                'longitude': data['ground_station_lon']
            }
        })
        response.headers.update(cors_headers())
        return response
    except Exception as e:
        return (jsonify({'error': str(e)}), 400, cors_headers())
