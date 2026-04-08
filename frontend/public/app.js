/**
 * Orbital Dynamics Frontend Application
 * Interactive learning platform for orbital mechanics
 * 
 * API Base URL is now managed by firebase-config.js
 * which automatically selects between local/Firebase endpoints
 */

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeEventHandlers();
    loadOrbitalCatalog();
    setupCesiumVisualization();
});

/**
 * Initialize all event handlers
 */
function initializeEventHandlers() {
    // Navigation
    document.querySelectorAll('[data-section]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.getAttribute('data-section');
            switchSection(section);
        });
    });

    // TLE Form
    document.getElementById('tle-form').addEventListener('submit', function(e) {
        e.preventDefault();
        parseTLE();
    });

    // Keplerian sliders
    const sliders = ['a', 'e', 'i', 'raan', 'aop', 'nu'];
    sliders.forEach(id => {
        const slider = document.getElementById(`slider-${id}`);
        if (slider) {
            slider.addEventListener('input', function() {
                updateKeplerianDisplay();
            });
        }
    });

    // Hohmann transfer form
    document.getElementById('hohmann-form').addEventListener('submit', function(e) {
        e.preventDefault();
        calculateHohmannTransfer();
    });
}

/**
 * Switch between sections
 */
function switchSection(section) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    
    // Show selected section
    const sectionElement = document.getElementById(section);
    if (sectionElement) {
        sectionElement.classList.add('active');
    }

    // Update navigation
    document.querySelectorAll('[data-section]').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('data-section') === section) {
            link.classList.add('active');
        }
    });

    // Trigger any necessary updates
    if (section === 'keplerian') {
        updateKeplerianDisplay();
    }
}

/**
 * Parse TLE from form input
 */
function parseTLE() {
    const name = document.getElementById('tle-name').value;
    const line1 = document.getElementById('tle-line1').value;
    const line2 = document.getElementById('tle-line2').value;

    apiCall('/tle/parse', 'POST', {
        name,
        line1,
        line2
    })
    .then(data => {
        if (data.error) {
            alert(`Error: ${data.error}`);
        } else {
            document.getElementById('tle-results').style.display = 'block';
            document.getElementById('tle-output').textContent = JSON.stringify(data, null, 2);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to parse TLE');
    });
}

/**
 * Update Keplerian display based on slider values
 */
function updateKeplerianDisplay() {
    const a = parseFloat(document.getElementById('slider-a').value);
    const e = parseFloat(document.getElementById('slider-e').value);
    const i = parseFloat(document.getElementById('slider-i').value);
    const raan = parseFloat(document.getElementById('slider-raan').value);
    const aop = parseFloat(document.getElementById('slider-aop').value);
    const nu = parseFloat(document.getElementById('slider-nu').value);

    // Update display values
    document.getElementById('value-a').textContent = a.toFixed(0);
    document.getElementById('value-e').textContent = e.toFixed(3);
    document.getElementById('value-i').textContent = i.toFixed(1);
    document.getElementById('value-raan').textContent = raan.toFixed(1);
    document.getElementById('value-aop').textContent = aop.toFixed(1);
    document.getElementById('value-nu').textContent = nu.toFixed(1);

    // Convert to state vectors
    apiCall('/conversions/keplerian-to-state', 'POST', {
        semi_major_axis_km: a,
        eccentricity: e,
        inclination_deg: i,
        raan_deg: raan,
        argument_of_perigee_deg: aop,
        true_anomaly_deg: nu
    })
    .then(data => {
        if (!data.error) {
            const r = data.position;
            const v = data.velocity;
            const r_mag = Math.sqrt(r[0]**2 + r[1]**2 + r[2]**2);
            const v_mag = Math.sqrt(v[0]**2 + v[1]**2 + v[2]**2);

            let info = `Cartesian State Vectors:
Position (ECI):
  X: ${r[0].toFixed(2)} km
  Y: ${r[1].toFixed(2)} km
  Z: ${r[2].toFixed(2)} km
  |r| = ${r_mag.toFixed(2)} km

Velocity (ECI):
  Vx: ${v[0].toFixed(4)} km/s
  Vy: ${v[1].toFixed(4)} km/s
  Vz: ${v[2].toFixed(4)} km/s
  |v| = ${v_mag.toFixed(4)} km/s

Orbital Parameters:
  Semi-major axis: ${a.toFixed(0)} km
  Eccentricity: ${e.toFixed(3)}
  Inclination: ${i.toFixed(1)}°
  Altitude (circular approx): ${(a - 6371).toFixed(0)} km`;

            document.getElementById('keplerian-output').textContent = info;
        }
    })
    .catch(error => console.error('Error:', error));
}

/**
 * Calculate Hohmann transfer
 */
function calculateHohmannTransfer() {
    const r1 = parseFloat(document.getElementById('hohmann-r1').value);
    const r2 = parseFloat(document.getElementById('hohmann-r2').value);

    apiCall('/maneuvers/hohmann', 'POST', {
        r1_km: r1,
        r2_km: r2
    })
    .then(data => {
        if (!data.error) {
                        const r1Km = data.r1_km ?? r1;
                        const r2Km = data.r2_km ?? r2;
                        const deltaV1 = data.delta_v1_km_s ?? data.delta_v_1_km_s;
                        const deltaV2 = data.delta_v2_km_s ?? data.delta_v_2_km_s;
                        const totalDeltaV = data.total_delta_v_km_s;
                        const transferMinutes = data.transfer_time_minutes ?? (data.transfer_time_seconds ? data.transfer_time_seconds / 60 : null);
                        const transferHours = data.transfer_time_hours ?? (transferMinutes !== null ? transferMinutes / 60 : null);
                        const transferSma = data.transfer_semi_major_axis_km ?? data.semi_major_axis_transfer;

            document.getElementById('hohmann-results').style.display = 'block';
            let output = `Hohmann Transfer Analysis:

Initial Orbit:
    Radius: ${r1Km.toFixed(0)} km
    Altitude: ${(r1Km - 6371).toFixed(0)} km

Final Orbit:
    Radius: ${r2Km.toFixed(0)} km
    Altitude: ${(r2Km - 6371).toFixed(0)} km

Transfer Maneuver:
    First Impulse (ΔV₁): ${deltaV1.toFixed(3)} km/s
    Second Impulse (ΔV₂): ${deltaV2.toFixed(3)} km/s
    Total ΔV: ${totalDeltaV.toFixed(3)} km/s
    Transfer Time: ${transferMinutes.toFixed(1)} minutes
    Transfer Time: ${transferHours.toFixed(2)} hours

Transfer Ellipse:
    Semi-major axis: ${transferSma.toFixed(0)} km
    Perigee: ${r1Km.toFixed(0)} km
    Apogee: ${r2Km.toFixed(0)} km`;

            document.getElementById('hohmann-output').textContent = output;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to calculate Hohmann transfer');
    });
}

/**
 * Load orbital catalog and display orbit types
 */
function loadOrbitalCatalog() {
    apiCall('/orbits/list')
    .then(data => {
        const container = document.getElementById('orbits-container');
        
        data.orbits.forEach(orbit_type => {
            apiCall('/orbits/info', 'POST', { orbit_type })
            .then(orbit_data => {
                const card = document.createElement('div');
                card.className = 'col-md-6 col-lg-4';
                card.innerHTML = `
                    <div class="card">
                        <div class="card-header">
                            <h5>${orbit_data.name}</h5>
                        </div>
                        <div class="card-body">
                            <p class="card-text">${orbit_data.description}</p>
                            
                            <h6>Characteristics:</h6>
                            <ul class="small">
                                <li>Typical Altitude: ${typeof orbit_data.typical_altitude_km === 'string' ? orbit_data.typical_altitude_km : orbit_data.typical_altitude_km + ' km'}</li>
                                <li>Eccentricity: ${orbit_data.typical_eccentricity}</li>
                                <li>Inclination: ${orbit_data.typical_inclination_deg}°</li>
                            </ul>
                            
                            <h6>Uses:</h6>
                            <ul class="small">
                                ${orbit_data.uses.map(u => `<li>${u}</li>`).join('')}
                            </ul>
                            
                            <h6>Example Satellites:</h6>
                            <ul class="small">
                                ${orbit_data.examples.slice(0, 2).map(ex => `<li>${ex.name} (${ex.country})</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                `;
                container.appendChild(card);
            })
            .catch(error => console.error(`Error loading ${orbit_type}:`, error));
        });
    })
    .catch(error => console.error('Error loading orbits:', error));
}

/**
 * Setup CesiumJS 3D Earth visualization
 */
function setupCesiumVisualization() {
    try {
        Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI3ZThjYTZkOC05ODI5LTQ0YjMtOWQwZi1mNzA1YTQ2NTA1YTIiLCJpZCI6MTczNDMsImlhdCI6MTY3NzcyNDU3MiwiZXhwIjoxNjc5MzMyNTcyLCJzdWJzY3JpcHRpb25JZCI6IjUyODI3IiwiYXNzZXRzIjpbXSwic2NvcGVzIjpbImFzbCIsImdjIl0sImNvbGxlY3Rpb25zIjpbIjM2ODczODciXSwibWFya2V0aW5nQ29tZXRzSWQiOndudWQsImlhdCI6MTY3NzcyNDU3Mn0.z6tclRZvXpz1zEXN2D7I4d8YUz47qXJGf6KxQmJ5sQ4';
        
        const viewer = new Cesium.Viewer('cesium-container', {
            terrainProvider: Cesium.createWorldTerrain(),
            imageryProvider: Cesium.ArcGisMapServerImageryProvider({
                url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer'
            })
        });

        // Add lighting
        viewer.scene.globe.enableLighting = true;

        // Position camera over Earth
        viewer.camera.setView({
            destination: Cesium.Cartesian3.fromDegrees(0, 0, 18000000)
        });

        // Add ISS marker (example)
        const issPt = Cesium.Cartesian3.fromDegrees(-77.036, 38.897, 400000);
        const issEntity = viewer.entities.add({
            position: issPt,
            point: {
                pixelSize: 8,
                color: Cesium.Color.RED
            },
            label: {
                text: 'ISS',
                font: '14pt monospace',
                outlineWidth: 2,
                outlineColor: Cesium.Color.WHITE,
                pixelOffset: new Cesium.Cartesian2(0, -14)
            }
        });

        // Enable animation
        viewer.clock.shouldAnimate = true;

        return viewer;
    } catch (error) {
        console.log('CesiumJS not available - visualization disabled');
    }
}

/**
 * Format large numbers with commas
 */
function formatNumber(num) {
    return num.toLocaleString('en-US', { 
        minimumFractionDigits: 0, 
        maximumFractionDigits: 2 
    });
}

/**
 * Utility: Convert degrees to radians
 */
function toRadians(degrees) {
    return degrees * Math.PI / 180;
}

/**
 * Utility: Convert radians to degrees
 */
function toDegrees(radians) {
    return radians * 180 / Math.PI;
}

// Make switchSection available globally for HTML onclick handlers
window.switchSection = switchSection;
