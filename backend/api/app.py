"""
Flask API Server for Orbital Dynamics Educational Website

Provides RESTful endpoints for:
- TLE parsing and propagation
- Orbital element conversions
- Maneuver calculations
- Ground track and access calculations
- Orbit catalog queries
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import numpy as np
import traceback
from datetime import datetime, timedelta
import json
import os

# Import orbital mechanics modules
from orbital_mechanics.tle import TLE, parse_tle_string, semi_major_axis_from_mean_motion
from orbital_mechanics.conversions import (
    cartesian_to_keplerian, keplerian_to_cartesian,
    mean_anomaly_to_true_anomaly, orbital_period, orbital_velocity
)
from orbital_mechanics.propagators import (
    TwoBodyPropagator, J2Propagator, compare_propagators
)
from orbital_mechanics.maneuvers import (
    HohmannTransfer, BiellipticTransfer, PlaneChange
)
from orbital_mechanics.ground_track import (
    GroundTrack, AccessCalculator, compute_horizon_distance
)
from orbital_mechanics.orbit_catalog import (
    get_orbit_info, list_all_orbits, calculate_orbital_period
)
from orbital_mechanics.constants import (
    EARTH_RADIUS_KM, GM_EARTH_KM3_S2, DEG_TO_RAD, RAD_TO_DEG
)
from orbital_mechanics.animation import (
    OrbitAnimationGenerator, GroundTrackAnimationGenerator
)
from orbital_mechanics.advanced_perturbations import (
    AdvancedPerturbationPropagator, LaunchWindowOptimizer
)
from orbital_mechanics.projections import (
    SinusoidalProjection, MollweideProjection,
    EquirectangularProjection, LambertAzimuthalProjection
)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Error handler
@app.errorhandler(Exception)
def handle_error(error):
    """Handle all errors and return JSON response."""
    print(f"Error: {error}")
    traceback.print_exc()
    return jsonify({
        'error': str(error),
        'type': type(error).__name__
    }), 400


# ============================================================================
# TLE Endpoints
# ============================================================================

@app.route('/api/tle/parse', methods=['POST'])
def tle_parse():
    """
    Parse TLE from input lines.
    
    Request JSON:
    {
        "name": "ISS",
        "line1": "1 25544U 98067A   21348.58768519  .00008803  00000-0  18458-3 0  9991",
        "line2": "2 25544  51.6439 260.8917 0002550  37.5917 322.5653 15.49207881317741"
    }
    """
    data = request.get_json()
    
    try:
        tle = TLE(data['line1'], data['line2'], data.get('name', 'UNKNOWN'))
        return jsonify(tle.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/tle/info', methods=['POST'])
def tle_info():
    """Get calculated info from TLE (semi-major axis, period, etc.)."""
    data = request.get_json()
    
    try:
        tle = TLE(data['line1'], data['line2'], data.get('name', 'UNKNOWN'))
        a = semi_major_axis_from_mean_motion(tle.mean_motion)
        period = orbital_period(a)
        altitude = a - EARTH_RADIUS_KM
        
        return jsonify({
            'satellite_name': tle.satellite_name,
            'semi_major_axis_km': a,
            'period_seconds': period,
            'period_minutes': period / 60.0,
            'altitude_km': altitude,
            'inclination_deg': tle.inclination,
            'eccentricity': tle.eccentricity,
            'mean_motion_rpm': tle.mean_motion,
            'bstar': tle.bstar
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ============================================================================
# Orbital Element Conversions
# ============================================================================

@app.route('/api/conversions/state-to-keplerian', methods=['POST'])
def state_to_keplerian():
    """Convert state vectors to Keplerian elements."""
    data = request.get_json()
    
    try:
        r_vec = np.array(data['position'])  # [x, y, z] in km
        v_vec = np.array(data['velocity'])  # [vx, vy, vz] in km/s
        mu = data.get('mu', GM_EARTH_KM3_S2)
        
        kep = cartesian_to_keplerian(r_vec, v_vec, mu)
        
        # Convert radians to degrees for output
        return jsonify({
            'semi_major_axis_km': float(kep['a']),
            'eccentricity': float(kep['e']),
            'inclination_deg': float(kep['i'] * RAD_TO_DEG),
            'raan_deg': float(kep['omega_cap'] * RAD_TO_DEG),
            'argument_of_perigee_deg': float(kep['omega'] * RAD_TO_DEG),
            'true_anomaly_deg': float(kep['nu'] * RAD_TO_DEG),
            'period_seconds': float(orbital_period(kep['a'], mu)),
            'period_minutes': float(orbital_period(kep['a'], mu) / 60.0)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/conversions/keplerian-to-state', methods=['POST'])
def keplerian_to_state():
    """Convert Keplerian elements to state vectors."""
    data = request.get_json()
    
    try:
        a = data['semi_major_axis_km']
        e = data['eccentricity']
        i = data['inclination_deg'] * DEG_TO_RAD
        omega_cap = data['raan_deg'] * DEG_TO_RAD
        omega = data['argument_of_perigee_deg'] * DEG_TO_RAD
        nu = data['true_anomaly_deg'] * DEG_TO_RAD
        mu = data.get('mu', GM_EARTH_KM3_S2)
        
        r_vec, v_vec = keplerian_to_cartesian(a, e, i, omega_cap, omega, nu, mu)
        
        return jsonify({
            'position': [float(r_vec[0]), float(r_vec[1]), float(r_vec[2])],
            'velocity': [float(v_vec[0]), float(v_vec[1]), float(v_vec[2])]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ============================================================================
# Orbital Maneuvers
# ============================================================================

@app.route('/api/maneuvers/hohmann', methods=['POST'])
def hohmann_transfer():
    """Calculate Hohmann transfer between two circular orbits."""
    data = request.get_json()
    
    try:
        r1 = data['r1_km']  # Initial orbit radius
        r2 = data['r2_km']  # Final orbit radius
        mu = data.get('mu', GM_EARTH_KM3_S2)
        
        transfer = HohmannTransfer(r1, r2, mu)
        return jsonify(transfer.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/maneuvers/bielliptic', methods=['POST'])
def bielliptic_transfer():
    """Calculate bi-elliptic transfer."""
    data = request.get_json()
    
    try:
        r1 = data['r1_km']
        r2 = data['r2_km']
        r_intermediate = data.get('r_intermediate_km')
        mu = data.get('mu', GM_EARTH_KM3_S2)
        
        transfer = BiellipticTransfer(r1, r2, r_intermediate, mu)
        return jsonify(transfer.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/maneuvers/plane-change', methods=['POST'])
def plane_change_maneuver():
    """Calculate plane change delta-v."""
    data = request.get_json()
    
    try:
        r = data['radius_km']
        delta_i_deg = data['delta_inclination_deg']
        delta_i_rad = delta_i_deg * DEG_TO_RAD
        mu = data.get('mu', GM_EARTH_KM3_S2)
        
        maneuver = PlaneChange(r, delta_i_rad, mu)
        
        return jsonify({
            'delta_v_km_s': maneuver.get_delta_v_simple(),
            'delta_inclination_deg': delta_i_deg
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ============================================================================
# Propagation
# ============================================================================

@app.route('/api/propagation/two-body', methods=['POST'])
def propagate_two_body():
    """Propagate orbit using two-body dynamics."""
    data = request.get_json()
    
    try:
        r_vec = np.array(data['position'])
        v_vec = np.array(data['velocity'])
        dt = data['time_seconds']
        mu = data.get('mu', GM_EARTH_KM3_S2)
        
        propagator = TwoBodyPropagator(r_vec, v_vec, mu)
        r_new, v_new = propagator.propagate(dt)
        
        return jsonify({
            'position': [float(r_new[0]), float(r_new[1]), float(r_new[2])],
            'velocity': [float(v_new[0]), float(v_new[1]), float(v_new[2])],
            'time_seconds': dt
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ============================================================================
# Ground Track and Access
# ============================================================================

@app.route('/api/ground-track/horizon-distance', methods=['POST'])
def horizon_dist():
    """Calculate horizon distance for satellite at given altitude."""
    data = request.get_json()
    
    try:
        altitude_km = data['altitude_km']
        distance = compute_horizon_distance(altitude_km)
        
        return jsonify({
            'altitude_km': altitude_km,
            'horizon_distance_km': distance,
            'horizon_distance_deg': distance / EARTH_RADIUS_KM * RAD_TO_DEG
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ============================================================================
# Orbit Catalog
# ============================================================================

@app.route('/api/orbits/list', methods=['GET'])
def list_orbits():
    """List all available orbit types."""
    return jsonify({
        'orbits': list_all_orbits()
    })


@app.route('/api/orbits/<orbit_type>', methods=['GET'])
def get_orbit(orbit_type):
    """Get detailed information about a specific orbit type."""
    try:
        info = get_orbit_info(orbit_type.upper())
        return jsonify(info)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404


@app.route('/api/orbits/period', methods=['POST'])
def get_period():
    """Calculate orbital period for given altitude."""
    data = request.get_json()
    
    try:
        altitude_km = data['altitude_km']
        period_minutes = calculate_orbital_period(altitude_km)
        
        return jsonify({
            'altitude_km': altitude_km,
            'period_seconds': period_minutes * 60.0,
            'period_minutes': period_minutes,
            'period_hours': period_minutes / 60.0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ============================================================================
# Real-time Animation and Visualization
# ============================================================================

@app.route('/api/animation/orbit-frames', methods=['POST'])
def animation_orbit_frames():
    """
    Generate orbit animation frames.
    
    Request JSON:
    {
        "initial_state": {"semi_major_axis_km": 7000, "eccentricity": 0.001, ...},
        "num_orbits": 1,
        "frames_per_orbit": 360
    }
    """
    from orbital_mechanics.animation import OrbitAnimationGenerator
    
    data = request.get_json()
    
    try:
        generator = OrbitAnimationGenerator(
            data.get('initial_state', {}),
            num_orbits=data.get('num_orbits', 1),
            frames_per_orbit=data.get('frames_per_orbit', 360)
        )
        
        frames = []
        for frame in generator.generate_frames():
            frames.append(frame)
        
        return jsonify({
            'total_frames': len(frames),
            'frames_per_orbit': data.get('frames_per_orbit', 360),
            'num_orbits': data.get('num_orbits', 1),
            'frames': frames
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/animation/ground-track-trace', methods=['POST'])
def animation_ground_track():
    """
    Generate ground track animation (sub-satellite points).
    
    Request JSON:
    {
        "satellite_tle": {"line1": "...", "line2": "..."},
        "start_datetime": "2024-01-01T00:00:00Z",
        "duration_minutes": 60,
        "step_seconds": 10
    }
    """
    from orbital_mechanics.animation import GroundTrackAnimationGenerator
    from orbital_mechanics.tle import TLE
    
    data = request.get_json()
    
    try:
        tle_data = data.get('satellite_tle', {})
        tle = TLE(tle_data['line1'], tle_data['line2'])
        
        # Create position function from TLE
        def get_position(dt):
            # Simple propagation from TLE
            from orbital_mechanics.live_tracking import propagate_tle
            try:
                pos, vel = propagate_tle(tle, dt)
                return pos
            except:
                return None
        
        start = datetime.fromisoformat(data['start_datetime'].replace('Z', '+00:00'))
        duration = data.get('duration_minutes', 60) * 60
        
        generator = GroundTrackAnimationGenerator(
            get_position,
            start,
            duration,
            step_seconds=data.get('step_seconds', 10)
        )
        
        frames = []
        for frame in generator.generate_frames():
            frames.append(frame)
        
        return jsonify({
            'total_frames': len(frames),
            'start_datetime': data['start_datetime'],
            'duration_minutes': data.get('duration_minutes', 60),
            'step_seconds': data.get('step_seconds', 10),
            'frames': frames
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/animation/comparative', methods=['POST'])
def animation_comparative():
    """
    Compare two-body vs J2-perturbed propagation.
    
    Request JSON:
    {
        "position": [rx, ry, rz],
        "velocity": [vx, vy, vz],
        "num_orbits": 1
    }
    """
    from orbital_mechanics.animation import ComparativeAnimationGenerator
    
    data = request.get_json()
    
    try:
        initial_state = {
            'position': np.array(data['position']),
            'velocity': np.array(data['velocity'])
        }
        
        generator = ComparativeAnimationGenerator(
            initial_state,
            num_orbits=data.get('num_orbits', 1),
            frames_per_orbit=data.get('frames_per_orbit', 360)
        )
        
        frames = []
        for frame in generator.generate_frames():
            frames.append(frame)
        
        return jsonify({
            'total_frames': len(frames),
            'num_orbits': data.get('num_orbits', 1),
            'comparison_note': 'Two-body vs J2-perturbed dynamics',
            'frames': frames[:100]  # Limit to first 100 frames for API
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ============================================================================
# Advanced Perturbations and High-Fidelity Propagation
# ============================================================================

@app.route('/api/perturbations/advanced', methods=['POST'])
def advanced_perturbations():
    """
    Propagate with advanced perturbations (J2, J3, J4, atmospheric drag).
    
    Request JSON:
    {
        "semi_major_axis_km": 7000,
        "eccentricity": 0.001,
        "inclination_deg": 51.6,
        "raan_deg": 0,
        "arg_perigee_deg": 0,
        "true_anomaly_deg": 0,
        "time_seconds": 3600,
        "ballistic_coefficient": 0.01
    }
    """
    from orbital_mechanics.advanced_perturbations import AdvancedPerturbationPropagator
    from orbital_mechanics.constants import DEG_TO_RAD
    
    data = request.get_json()
    
    try:
        propagator = AdvancedPerturbationPropagator(
            a=data['semi_major_axis_km'],
            e=data['eccentricity'],
            i=data['inclination_deg'] * DEG_TO_RAD,
            omega_cap=data.get('raan_deg', 0) * DEG_TO_RAD,
            omega=data.get('arg_perigee_deg', 0) * DEG_TO_RAD,
            nu=data.get('true_anomaly_deg', 0) * DEG_TO_RAD,
            include_drag=data.get('include_drag', True),
            ballistic_coefficient=data.get('ballistic_coefficient', 0.01)
        )
        
        result = propagator.propagate(data['time_seconds'])
        summary = propagator.get_perturbation_summary()
        
        return jsonify({
            'initial_elements': {
                'semi_major_axis_km': data['semi_major_axis_km'],
                'eccentricity': data['eccentricity'],
                'inclination_deg': data['inclination_deg']
            },
            'propagation_time_seconds': data['time_seconds'],
            'final_elements': {
                'semi_major_axis_km': float(result['a']),
                'eccentricity': float(result['e']),
                'inclination_deg': float(result['i'] * 180 / np.pi),
                'raan_deg': float(result['omega_cap'] * 180 / np.pi),
                'arg_perigee_deg': float(result['omega'] * 180 / np.pi),
                'true_anomaly_deg': float(result['nu'] * 180 / np.pi)
            },
            'perturbation_rates': summary
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ============================================================================
# Map Projections
# ============================================================================

@app.route('/api/projections/list', methods=['GET'])
def list_projections():
    """List available map projections."""
    return jsonify({
        'projections': [
            'sinusoidal',
            'mollweide',
            'equirectangular',
            'lambert_azimuthal'
        ],
        'recommended': 'sinusoidal',
        'notes': 'Sinusoidal: equal-area, NASA standard; Mollweide: whole-Earth; Equirectangular: simple; Lambert Azimuthal: polar-optimized'
    })


@app.route('/api/projections/project', methods=['POST'])
def project_coordinates():
    """
    Project geographic coordinates using specified projection.
    
    Request JSON:
    {
        "projection": "sinusoidal",
        "latitude_deg": 51.6,
        "longitude_deg": 0
    }
    """
    from orbital_mechanics.projections import (
        SinusoidalProjection, MollweideProjection,
        EquirectangularProjection, LambertAzimuthalProjection
    )
    from orbital_mechanics.constants import DEG_TO_RAD
    
    data = request.get_json()
    
    try:
        projection_type = data['projection'].lower()
        lat = data['latitude_deg'] * DEG_TO_RAD
        lon = data['longitude_deg'] * DEG_TO_RAD
        
        projection_map = {
            'sinusoidal': SinusoidalProjection(2000, 1000),
            'mollweide': MollweideProjection(2000, 1000),
            'equirectangular': EquirectangularProjection(2000, 1000),
            'lambert_azimuthal': LambertAzimuthalProjection(2000, 1000)
        }
        
        proj = projection_map.get(projection_type, SinusoidalProjection(2000, 1000))
        x, y = proj.project(lat, lon)
        
        return jsonify({
            'projection': projection_type,
            'input_latitude_deg': data['latitude_deg'],
            'input_longitude_deg': data['longitude_deg'],
            'projected_x': float(x),
            'projected_y': float(y),
            'canvas_width': 2000,
            'canvas_height': 1000
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ============================================================================
# Mission Planning
# ============================================================================

@app.route('/api/mission-planning/launch-windows', methods=['POST'])
def launch_windows():
    """
    Compute feasible launch windows for target orbit.
    
    Request JSON:
    {
        "launch_site_latitude_deg": 28.5,
        "launch_site_longitude_deg": -80.5,
        "target_inclination_deg": 51.6,
        "start_date": "2024-01-01",
        "num_days": 7
    }
    """
    from orbital_mechanics.advanced_perturbations import LaunchWindowOptimizer
    from orbital_mechanics.constants import DEG_TO_RAD
    
    data = request.get_json()
    
    try:
        from datetime import datetime, timedelta
        
        optimizer = LaunchWindowOptimizer(
            data['launch_site_latitude_deg'],
            data.get('target_inclination_deg', 51.6)
        )
        
        start_date = datetime.fromisoformat(data['start_date'])
        num_days = data.get('num_days', 7)
        
        windows = optimizer.compute_launch_windows(start_date, num_days)
        
        return jsonify({
            'launch_site_latitude_deg': data['launch_site_latitude_deg'],
            'target_inclination_deg': data.get('target_inclination_deg', 51.6),
            'num_days': num_days,
            'start_date': data['start_date'],
            'windows': windows,
            'total_windows': len(windows)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ============================================================================
# Health Check
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'Orbital Dynamics API'
    })


# ============================================================================
# Frontend Serving (for Replit and local deployment)
# ============================================================================

@app.route('/')
def serve_index():
    """Serve main HTML file."""
    try:
        frontend_path = os.path.join(os.path.dirname(__file__), '../../frontend/public')
        return send_from_directory(frontend_path, 'index.html')
    except Exception as e:
        return jsonify({'error': 'Frontend not found', 'details': str(e)}), 404


@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files (JS, CSS, images, etc)."""
    try:
        frontend_path = os.path.join(os.path.dirname(__file__), '../../frontend/public')
        return send_from_directory(frontend_path, filename)
    except Exception as e:
        # Fallback: serve index for SPA routing
        try:
            frontend_path = os.path.join(os.path.dirname(__file__), '../../frontend/public')
            return send_from_directory(frontend_path, 'index.html')
        except:
            return jsonify({'error': 'Asset not found', 'file': filename}), 404


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    print("Starting Orbital Dynamics API Server...")
    print("Available endpoints:")
    print()
    print("=== Health & Info ===")
    print("  GET  /api/health")
    print()
    print("=== TLE Operations ===")
    print("  POST /api/tle/parse")
    print("  POST /api/tle/info")
    print()
    print("=== Orbital Element Conversions ===")
    print("  POST /api/conversions/state-to-keplerian")
    print("  POST /api/conversions/keplerian-to-state")
    print()
    print("=== Orbital Maneuvers ===")
    print("  POST /api/maneuvers/hohmann")
    print("  POST /api/maneuvers/bielliptic")
    print("  POST /api/maneuvers/plane-change")
    print()
    print("=== Propagation ===")
    print("  POST /api/propagation/two-body")
    print()
    print("=== Real-time Animation [NEW] ===")
    print("  POST /api/animation/orbit-frames")
    print("  POST /api/animation/ground-track-trace")
    print("  POST /api/animation/comparative")
    print()
    print("=== Advanced Perturbations [NEW] ===")
    print("  POST /api/perturbations/advanced")
    print()
    print("=== Map Projections [NEW] ===")
    print("  GET  /api/projections/list")
    print("  POST /api/projections/project")
    print()
    print("=== Mission Planning [NEW] ===")
    print("  POST /api/mission-planning/launch-windows")
    print()
    print("=== Orbit Catalog ===")
    print("  GET  /api/orbits/list")
    print("  GET  /api/orbits/<type>")
    print("  POST /api/orbits/period")
    print()
    print("=== Ground Track & Access ===")
    print("  POST /api/ground-track/horizon-distance")
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
