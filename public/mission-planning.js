/**
 * Mission Planning Module
 * 
 * Provides interface for:
 * - Launch window calculation and optimization
 * - Mission parameter selection
 * - Delta-v budgeting
 * - Feasibility analysis
 */

/**
 * Compute launch windows for selected mission
 */
async function computeLaunchWindows() {
    const form = document.getElementById('mission-planning-form');
    if (!form) return;
    
    // Get form values
    const launchSiteLat = parseFloat(document.getElementById('launch-site-lat')?.value || 28.5);
    const launchSiteLon = parseFloat(document.getElementById('launch-site-lon')?.value || -80.5);
    const targetInclination = parseFloat(document.getElementById('target-inclination')?.value || 51.6);
    const startDate = document.getElementById('start-date')?.value || new Date().toISOString().split('T')[0];
    const numDays = parseInt(document.getElementById('num-days')?.value || 7);
    
    const loadingDiv = document.getElementById('launch-windows-loading');
    if (loadingDiv) loadingDiv.style.display = 'block';
    
    try {
        const data = await apiCall('/mission-planning/launch-windows', 'POST', {
            launch_site_latitude_deg: launchSiteLat,
            launch_site_longitude_deg: launchSiteLon,
            target_inclination_deg: targetInclination,
            start_date: startDate,
            num_days: numDays
        });
        
        displayLaunchWindows(data);
        
    } catch (error) {
        console.error('Launch window computation failed:', error);
        alert('Failed to compute launch windows');
    } finally {
        if (loadingDiv) loadingDiv.style.display = 'none';
    }
}


/**
 * Display launch windows in UI
 * 
 * @param {Object} data - Launch window data from API
 */
function displayLaunchWindows(data) {
    const resultsDiv = document.getElementById('launch-windows-results');
    if (!resultsDiv) return;
    
    if (!data.windows || data.windows.length === 0) {
        resultsDiv.innerHTML = '<p>No launch windows found for selected parameters</p>';
        return;
    }
    
    let html = `
        <div class="launch-windows-summary">
            <p><strong>Launch Site:</strong> Lat ${data.launch_site_latitude_deg}°, Lon ${data.launch_site_longitude_deg}°</p>
            <p><strong>Target Inclination:</strong> ${data.target_inclination_deg}°</p>
            <p><strong>Period:</strong> ${data.start_date} to +${data.num_days} days</p>
            <p><strong>Total Windows Found:</strong> ${data.total_windows}</p>
        </div>
        <table class="windows-table">
            <thead>
                <tr>
                    <th>Date/Time (UTC)</th>
                    <th>Azimuth (°)</th>
                    <th>Azimuth Constraint (°)</th>
                    <th>Delta-V (km/s)</th>
                    <th>Feasibility</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    for (let window of data.windows) {
        const feasibility = window.feasible ? '✓ Feasible' : '✗ Infeasible';
        const feasibilityClass = window.feasible ? 'feasible' : 'infeasible';
        
        html += `
            <tr class="${feasibilityClass}">
                <td>${window.datetime}</td>
                <td>${window.azimuth_deg?.toFixed(1) || 'N/A'}</td>
                <td>${window.azimuth_constraint_deg?.toFixed(1) || 'N/A'}</td>
                <td>${window.delta_v_estimate_km_s?.toFixed(3) || 'N/A'}</td>
                <td>${feasibility}</td>
            </tr>
        `;
    }
    
    html += `
            </tbody>
        </table>
    `;
    
    resultsDiv.innerHTML = html;
}


/**
 * Advanced perturbation analysis for mission
 */
async function analyzePerturbations() {
    const form = document.getElementById('perturbations-form');
    if (!form) return;
    
    const sma = parseFloat(document.getElementById('mission-sma')?.value || 7000);
    const ecc = parseFloat(document.getElementById('mission-ecc')?.value || 0.001);
    const incl = parseFloat(document.getElementById('mission-incl')?.value || 51.6);
    const raan = parseFloat(document.getElementById('mission-raan')?.value || 0);
    const aop = parseFloat(document.getElementById('mission-aop')?.value || 0);
    const nu = parseFloat(document.getElementById('mission-nu')?.value || 0);
    const propTime = parseFloat(document.getElementById('prop-time-hours')?.value || 1) * 3600;
    const ballCoeff = parseFloat(document.getElementById('ballistic-coefficient')?.value || 0.01);
    
    const loadingDiv = document.getElementById('perturbations-loading');
    if (loadingDiv) loadingDiv.style.display = 'block';
    
    try {
        const data = await apiCall('/perturbations/advanced', 'POST', {
            semi_major_axis_km: sma,
            eccentricity: ecc,
            inclination_deg: incl,
            raan_deg: raan,
            arg_perigee_deg: aop,
            true_anomaly_deg: nu,
            time_seconds: propTime,
            include_drag: true,
            ballistic_coefficient: ballCoeff
        });
        
        displayPerturbationResults(data);
        
    } catch (error) {
        console.error('Perturbation analysis failed:', error);
        alert('Failed to analyze perturbations');
    } finally {
        if (loadingDiv) loadingDiv.style.display = 'none';
    }
}


/**
 * Display perturbation analysis results
 * 
 * @param {Object} data - Perturbation analysis data
 */
function displayPerturbationResults(data) {
    const resultsDiv = document.getElementById('perturbations-results');
    if (!resultsDiv) return;
    
    const initial = data.initial_elements;
    const final = data.final_elements;
    const rates = data.perturbation_rates;
    
    // Calculate changes
    const deltA = final.semi_major_axis_km - initial.semi_major_axis_km;
    const deltE = final.eccentricity - initial.eccentricity;
    const deltI = final.inclination_deg - initial.inclination_deg;
    
    let html = `
        <div class="perturbation-results">
            <h3>High-Fidelity Propagation Results (J2 + J3 + J4 + Drag)</h3>
            
            <div class="results-section">
                <h4>Initial State</h4>
                <p>Semi-major axis: ${initial.semi_major_axis_km.toFixed(2)} km</p>
                <p>Eccentricity: ${initial.eccentricity.toFixed(6)}</p>
                <p>Inclination: ${initial.inclination_deg.toFixed(4)}°</p>
            </div>
            
            <div class="results-section">
                <h4>Final State (after ${(data.propagation_time_seconds / 3600).toFixed(1)} hours)</h4>
                <p>Semi-major axis: ${final.semi_major_axis_km.toFixed(2)} km (Δa = ${deltA.toFixed(3)} km)</p>
                <p>Eccentricity: ${final.eccentricity.toFixed(6)} (Δe = ${deltE.toFixed(6)})</p>
                <p>Inclination: ${final.inclination_deg.toFixed(4)}° (Δi = ${deltI.toFixed(6)}°)</p>
                <p>RAAN: ${final.raan_deg.toFixed(4)}°</p>
                <p>Argument of Perigee: ${final.arg_perigee_deg.toFixed(4)}°</p>
                <p>True Anomaly: ${final.true_anomaly_deg.toFixed(4)}°</p>
            </div>
            
            <div class="results-section">
                <h4>Perturbation Effects (rate per orbit)</h4>
    `;
    
    if (rates) {
        html += `<p>J2 RAAN precession: ${rates.j2_raan_rate_deg_per_day?.toFixed(4) || 'N/A'}°/day</p>`;
        html += `<p>J2 argument of perigee: ${rates.j2_aop_rate_deg_per_day?.toFixed(4) || 'N/A'}°/day</p>`;
        html += `<p>J3 effect on RAAN: ${rates.j3_contribution_deg_per_day?.toFixed(6) || 'N/A'}°/day</p>`;
        html += `<p>J4 effect on RAAN: ${rates.j4_contribution_deg_per_day?.toFixed(6) || 'N/A'}°/day</p>`;
        html += `<p>Atmospheric drag rate: ${rates.drag_rate_km_per_day?.toFixed(4) || 'N/A'} km/day</p>`;
    }
    
    html += `
            </div>
        </div>
    `;
    
    resultsDiv.innerHTML = html;
}


/**
 * Calculate total mission delta-v budget
 * 
 * @param {Object} mission - Mission parameters
 */
function calculateMissionDeltaV(mission) {
    let totalDeltaV = 0;
    let breakdown = {};
    
    // Launch to orbit
    const launchDeltaV = mission.launch_delta_v || 9.3;
    breakdown['Launch to Orbit'] = launchDeltaV;
    totalDeltaV += launchDeltaV;
    
    // Orbital maneuvers
    if (mission.hohmann_transfers) {
        for (let transfer of mission.hohmann_transfers) {
            breakdown[`Hohmann Transfer (${transfer.name})`] = transfer.delta_v_km_s;
            totalDeltaV += transfer.delta_v_km_s;
        }
    }
    
    // Station-keeping
    const stationKeepingDeltaV = mission.station_keeping_delta_v || 0.5;
    breakdown['Station Keeping'] = stationKeepingDeltaV;
    totalDeltaV += stationKeepingDeltaV;
    
    // Disposal/deorbit
    const diposalDeltaV = mission.disposal_delta_v || 0.2;
    breakdown['Disposal'] = diposalDeltaV;
    totalDeltaV += diposalDeltaV;
    
    return {
        total: totalDeltaV,
        breakdown: breakdown
    };
}


/**
 * Estimate mission cost (simplified model)
 * 
 * @param {Object} mission - Mission parameters
 */
function estimateMissionCost(mission) {
    // Simplified cost model: cost per kg * mass * complexity factor
    const costPerKg = mission.cost_per_kg || 5000; // $/kg to LEO
    const spacecraftMass = mission.spacecraft_mass_kg || 1000;
    const complexityFactor = mission.complexity_factor || 1.5;
    
    const totalCost = costPerKg * spacecraftMass * complexityFactor;
    
    return {
        total_cost_usd: totalCost,
        cost_per_day: totalCost / (mission.mission_duration_days || 365),
        cost_per_kg: costPerKg
    };
}


/**
 * Export mission plan to JSON
 */
function exportMissionPlan() {
    const mission = {
        planning_date: new Date().toISOString(),
        launch_site: {
            latitude: parseFloat(document.getElementById('launch-site-lat')?.value || 28.5),
            longitude: parseFloat(document.getElementById('launch-site-lon')?.value || -80.5)
        },
        target_orbit: {
            semi_major_axis_km: parseFloat(document.getElementById('mission-sma')?.value || 7000),
            eccentricity: parseFloat(document.getElementById('mission-ecc')?.value || 0.001),
            inclination_deg: parseFloat(document.getElementById('mission-incl')?.value || 51.6)
        },
        spacecraft: {
            mass_kg: parseFloat(document.getElementById('spacecraft-mass')?.value || 1000),
            ballistic_coefficient: parseFloat(document.getElementById('ballistic-coefficient')?.value || 0.01)
        },
        analysis_timestamp: new Date().toISOString()
    };
    
    // Download JSON
    const jsonStr = JSON.stringify(mission, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `mission-plan-${Date.now()}.json`;
    link.click();
    window.URL.revokeObjectURL(url);
}


/**
 * Update mission summary display
 */
function updateMissionSummary() {
    const summaryDiv = document.getElementById('mission-summary');
    if (!summaryDiv) return;
    
    const sma = parseFloat(document.getElementById('mission-sma')?.value || 7000);
    const ecc = parseFloat(document.getElementById('mission-ecc')?.value || 0.001);
    const incl = parseFloat(document.getElementById('mission-incl')?.value || 51.6);
    const mass = parseFloat(document.getElementById('spacecraft-mass')?.value || 1000);
    
    // Calculate orbital period
    const mu = 398600.4418; // Earth's GM in km^3/s^2
    const period = 2 * Math.PI * Math.sqrt(Math.pow(sma, 3) / mu) / 60; // minutes
    
    const altitude = sma - 6371; // Earth radius
    
    let html = `
        <div class="mission-summary-box">
            <h4>Mission Summary</h4>
            <p><strong>Orbit Type:</strong> ${getOrbitClass(sma, ecc)}</p>
            <p><strong>Semi-major Axis:</strong> ${sma.toFixed(0)} km</p>
            <p><strong>Altitude (circular approx):</strong> ${altitude.toFixed(0)} km</p>
            <p><strong>Eccentricity:</strong> ${ecc.toFixed(6)}</p>
            <p><strong>Inclination:</strong> ${incl.toFixed(2)}°</p>
            <p><strong>Orbital Period:</strong> ${period.toFixed(2)} minutes</p>
            <p><strong>Spacecraft Mass:</strong> ${mass.toFixed(0)} kg</p>
        </div>
    `;
    
    summaryDiv.innerHTML = html;
}


/**
 * Classify orbit type based on parameters
 * 
 * @param {number} sma - Semi-major axis in km
 * @param {number} ecc - Eccentricity
 */
function getOrbitClass(sma, ecc) {
    const altitude = sma - 6371;
    
    if (altitude < 2000) return 'LEO (Low Earth Orbit)';
    if (altitude < 12000) return 'LEO (Low Earth Orbit)';
    if (altitude < 20000) return 'MEO (Medium Earth Orbit)';
    if (altitude < 40000) return 'GEO Transfer Orbit';
    if (Math.abs(sma - 42164) < 1000) return 'GEO (Geostationary Orbit)';
    if (altitude > 40000) return 'HEO (High Earth Orbit)';
    
    return 'Unknown';
}


/**
 * Initialize mission planning UI
 */
function initializeMissionPlanning() {
    // Set up event listeners
    const computeBtn = document.getElementById('compute-windows-btn');
    if (computeBtn) {
        computeBtn.addEventListener('click', computeLaunchWindows);
    }
    
    const analyzeBtn = document.getElementById('analyze-perturbations-btn');
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', analyzePerturbations);
    }
    
    const exportBtn = document.getElementById('export-mission-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportMissionPlan);
    }
    
    // Update summary on input changes
    const inputIds = ['mission-sma', 'mission-ecc', 'mission-incl', 'spacecraft-mass'];
    inputIds.forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            input.addEventListener('change', updateMissionSummary);
            input.addEventListener('input', updateMissionSummary);
        }
    });
    
    // Initial summary display
    updateMissionSummary();
}
