/**
 * Real-time Orbit Animation Module
 * 
 * Provides animation infrastructure for:
 * - Live orbit propagation visualization
 * - Ground track tracing
 * - Comparative propagator analysis
 */

// Animation state
let animationState = {
    isRunning: false,
    isPaused: false,
    currentFrame: 0,
    totalFrames: 0,
    frames: [],
    startTime: null,
    animationId: null
};

let cesiumAnimationEntity = null;


/**
 * Initialize real-time animation for orbit
 * 
 * @param {Array} frames - Animation frames array from API
 * @param {number} speedFactor - Animation speed multiplier (default: 1)
 */
function initializeOrbitAnimation(frames, speedFactor = 1) {
    animationState.frames = frames;
    animationState.totalFrames = frames.length;
    animationState.currentFrame = 0;
    animationState.isRunning = true;
    animationState.isPaused = false;
    animationState.speedFactor = speedFactor;
    animationState.startTime = Date.now();
    
    // Create animation entity in Cesium
    if (window.viewer) {
        createAnimationEntity(frames);
    }
    
    // Start animation loop
    animateFrame();
    
    // Update UI controls
    updateAnimationControls();
}


/**
 * Create Cesium entity for animated orbit
 * 
 * @param {Array} frames - Animation frames
 */
function createAnimationEntity(frames) {
    if (!viewer) return;
    
    // Remove previous animation entity
    if (cesiumAnimationEntity) {
        viewer.entities.remove(cesiumAnimationEntity);
    }
    
    // Extract positions from frames
    const positions = Cesium.Cartesian3.fromDegreesArrayHeights([]);
    
    for (let frame of frames) {
        const r = frame.position_eci;
        if (r && r.length === 3) {
            // Convert ECI to ECEF (simplified: add Earth's rotation)
            const pos = Cesium.Cartesian3.fromArray(r);
            positions.push(pos);
        }
    }
    
    if (positions.length === 0) return;
    
    // Create path geometry
    cesiumAnimationEntity = viewer.entities.add({
        name: 'Animated Orbit',
        polyline: {
            positions: new Cesium.CallbackProperty(() => {
                const current = animationState.frames[animationState.currentFrame];
                if (!current || !current.position_eci) return [];
                const r = current.position_eci;
                return [Cesium.Cartesian3.fromArray(r)];
            }, false),
            width: 2,
            material: Cesium.Color.CYAN,
            clampToGround: false
        },
        point: {
            pixelSize: 8,
            color: Cesium.Color.CYAN,
            outlineColor: Cesium.Color.WHITE,
            outlineWidth: 2
        }
    });
    
    viewer.zoomTo(cesiumAnimationEntity);
}


/**
 * Animation loop frame updater
 */
function animateFrame() {
    if (!animationState.isRunning || animationState.isPaused) {
        animationState.animationId = requestAnimationFrame(animateFrame);
        return;
    }
    
    if (animationState.currentFrame >= animationState.totalFrames) {
        animationState.isRunning = false;
        updateAnimationControls();
        console.log('Animation complete');
        return;
    }
    
    // Get current frame
    const frame = animationState.frames[animationState.currentFrame];
    
    // Update visualization
    if (cesiumAnimationEntity && frame.position_eci) {
        const r = frame.position_eci;
        cesiumAnimationEntity.position = new Cesium.CallbackProperty(() => {
            return Cesium.Cartesian3.fromArray(r);
        }, false);
    }
    
    // Update UI display
    displayFrameInfo(frame);
    
    // Increment frame with speed factor
    animationState.currentFrame += animationState.speedFactor || 1;
    
    // Continue animation
    animationState.animationId = requestAnimationFrame(animateFrame);
}


/**
 * Play animation
 */
function playAnimation() {
    if (animationState.frames.length === 0) {
        console.warn('No animation frames loaded');
        return;
    }
    animationState.isRunning = true;
    animationState.isPaused = false;
    animateFrame();
    updateAnimationControls();
}


/**
 * Pause animation
 */
function pauseAnimation() {
    animationState.isPaused = true;
    updateAnimationControls();
}


/**
 * Resume animation
 */
function resumeAnimation() {
    animationState.isPaused = false;
    animateFrame();
    updateAnimationControls();
}


/**
 * Stop animation and reset
 */
function stopAnimation() {
    animationState.isRunning = false;
    animationState.isPaused = false;
    animationState.currentFrame = 0;
    if (animationState.animationId) {
        cancelAnimationFrame(animationState.animationId);
    }
    updateAnimationControls();
}


/**
 * Set animation speed multiplier
 * 
 * @param {number} factor - Speed factor (0.5x, 1x, 2x, 4x)
 */
function setAnimationSpeed(factor) {
    animationState.speedFactor = factor;
    document.getElementById('speed-label').textContent = `${factor}x`;
}


/**
 * Jump to specific frame
 * 
 * @param {number} frameNumber - Frame number to jump to
 */
function jumpToFrame(frameNumber) {
    if (frameNumber >= 0 && frameNumber < animationState.totalFrames) {
        animationState.currentFrame = frameNumber;
        const frame = animationState.frames[frameNumber];
        displayFrameInfo(frame);
    }
}


/**
 * Display current frame information
 * 
 * @param {Object} frame - Frame data
 */
function displayFrameInfo(frame) {
    if (!frame) return;
    
    const infoDiv = document.getElementById('animation-info');
    if (!infoDiv) return;
    
    let html = `
        <div class="frame-info">
            <p><strong>Frame:</strong> ${animationState.currentFrame + 1} / ${animationState.totalFrames}</p>
            <p><strong>Time:</strong> ${(frame.time_seconds / 3600).toFixed(2)} hours</p>
    `;
    
    if (frame.altitude_km) {
        html += `<p><strong>Altitude:</strong> ${frame.altitude_km.toFixed(0)} km</p>`;
    }
    
    if (frame.true_anomaly_deg) {
        html += `<p><strong>True Anomaly:</strong> ${frame.true_anomaly_deg.toFixed(1)}°</p>`;
    }
    
    if (frame.velocity_magnitude_km_s) {
        html += `<p><strong>Velocity:</strong> ${frame.velocity_magnitude_km_s.toFixed(3)} km/s</p>`;
    }
    
    html += `</div>`;
    infoDiv.innerHTML = html;
}


/**
 * Update animation control buttons UI
 */
function updateAnimationControls() {
    const playBtn = document.getElementById('btn-play');
    const pauseBtn = document.getElementById('btn-pause');
    const resumeBtn = document.getElementById('btn-resume');
    const stopBtn = document.getElementById('btn-stop');
    
    if (playBtn) playBtn.disabled = animationState.isRunning;
    if (pauseBtn) pauseBtn.disabled = !animationState.isRunning || animationState.isPaused;
    if (resumeBtn) resumeBtn.disabled = !animationState.isPaused;
    if (stopBtn) stopBtn.disabled = !animationState.isRunning && animationState.currentFrame === 0;
}


/**
 * Request orbit animation from API and start playback
 * 
 * @param {Object} orbitParams - Orbital parameters
 */
async function requestAndPlayAnimation(orbitParams) {
    const loadingDiv = document.getElementById('animation-loading');
    if (loadingDiv) loadingDiv.style.display = 'block';
    
    try {
        const data = await apiCall('/animation/orbit-frames', 'POST', orbitParams);
        
        if (data.error) throw new Error(data.error);
        
        console.log(`Received ${data.frames.length} animation frames`);
        
        // Initialize animation
        initializeOrbitAnimation(data.frames, 1);
        
        // Show animation controls
        const controlsDiv = document.getElementById('animation-controls');
        if (controlsDiv) controlsDiv.style.display = 'block';
        
    } catch (error) {
        console.error('Animation request failed:', error);
        alert('Failed to load animation frames');
    } finally {
        if (loadingDiv) loadingDiv.style.display = 'none';
    }
}


/**
 * Request ground track animation from API
 * 
 * @param {Object} groundTrackParams - Ground track parameters
 */
async function requestGroundTrackAnimation(groundTrackParams) {
    try {
        const data = await apiCall('/animation/ground-track-trace', 'POST', groundTrackParams);
        
        if (data.error) throw new Error(data.error);
        
        console.log(`Ground track has ${data.frames.length} points`);
        
        // Create ground track visualization
        displayGroundTrack(data.frames);
        
    } catch (error) {
        console.error('Ground track request failed:', error);
    }
}


/**
 * Display ground track on map
 * 
 * @param {Array} frames - Ground track frames
 */
function displayGroundTrack(frames) {
    if (!viewer) return;
    
    const positions = [];
    
    for (let frame of frames) {
        const cartographic = Cesium.Cartographic.fromDegrees(
            frame.longitude_deg,
            frame.latitude_deg,
            0
        );
        positions.push(Cesium.Cartesian3.fromCartographic(cartographic));
    }
    
    if (positions.length < 2) return;
    
    viewer.entities.add({
        name: 'Ground Track',
        polyline: {
            positions: positions,
            width: 2,
            material: Cesium.Color.RED,
            clampToGround: true
        }
    });
    
    // Zoom to ground track
    viewer.zoomTo(viewer.entities.getById('Ground Track'));
}


/**
 * Request and display comparative propagation visualization
 * 
 * @param {Object} stateVector - Initial state vector [position, velocity]
 */
async function requestComparativeAnimation(stateVector) {
    try {
        const data = await apiCall('/animation/comparative', 'POST', {
            position: stateVector.position,
            velocity: stateVector.velocity,
            num_orbits: 1
        });
        
        if (data.error) throw new Error(data.error);
        
        console.log('Comparative animation data received');
        
        // Display comparison metrics
        displayComparativeMetrics(data.frames);
        
    } catch (error) {
        console.error('Comparative animation request failed:', error);
    }
}


/**
 * Display comparative propagation metrics
 * 
 * @param {Array} frames - Comparative frames data
 */
function displayComparativeMetrics(frames) {
    const metricsDiv = document.getElementById('comparative-metrics');
    if (!metricsDiv) return;
    
    let maxDivergence = 0;
    let maxRAANDiff = 0;
    
    for (let frame of frames) {
        if (frame.position_divergence_km > maxDivergence) {
            maxDivergence = frame.position_divergence_km;
        }
        if (frame.raan_difference_deg > maxRAANDiff) {
            maxRAANDiff = frame.raan_difference_deg;
        }
    }
    
    const html = `
        <div class="comparison-results">
            <p><strong>Two-Body vs J2 Perturbation Comparison</strong></p>
            <p>Max Position Divergence: ${maxDivergence.toFixed(2)} km</p>
            <p>Max RAAN Difference: ${maxRAANDiff.toFixed(4)}°</p>
            <p>Total Frames: ${frames.length}</p>
        </div>
    `;
    
    metricsDiv.innerHTML = html;
}


/**
 * Export animation frames to CSV
 */
function exportAnimationFrames() {
    if (animationState.frames.length === 0) {
        alert('No animation frames to export');
        return;
    }
    
    // Create CSV content
    let csv = 'Frame,Time (s),X (km),Y (km),Z (km),Vx (km/s),Vy (km/s),Vz (km/s),Altitude (km),TrueAnomaly (°)\n';
    
    for (let frame of animationState.frames) {
        const r = frame.position_eci || [];
        const v = frame.velocity_eci || [];
        csv += `${frame.frame},${frame.time_seconds},${r[0]},${r[1]},${r[2]},${v[0]},${v[1]},${v[2]},${frame.altitude_km},${frame.true_anomaly_deg}\n`;
    }
    
    // Download CSV
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `orbit-animation-${Date.now()}.csv`;
    link.click();
    window.URL.revokeObjectURL(url);
}
