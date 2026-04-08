/**
 * Map Projections Frontend Module
 * 
 * Provides 2D map visualization with multiple projection methods:
 * - Sinusoidal (equal-area, NASA standard)
 * - Mollweide (whole-Earth elliptical)
 * - Equirectangular (simple cylindrical)
 * - Lambert Azimuthal (polar-optimized)
 */

let projectionState = {
    currentProjection: 'sinusoidal',
    canvas: null,
    context: null,
    width: 1200,
    height: 600,
    groundTrackPoints: [],
    accessWindows: []
};


/**
 * Initialize 2D ground track map
 */
function initializeGroundTrackMap() {
    const mapDiv = document.getElementById('ground-track-map-canvas');
    if (!mapDiv) return;
    
    // Create canvas
    const canvas = document.createElement('canvas');
    canvas.width = projectionState.width;
    canvas.height = projectionState.height;
    canvas.style.border = '1px solid #ccc';
    canvas.style.backgroundColor = '#e3f2fd';
    
    mapDiv.appendChild(canvas);
    
    projectionState.canvas = canvas;
    projectionState.context = canvas.getContext('2d');
    
    // Draw base map
    drawMapProjection();
    
    // Setup projection selector
    const projectionSelect = document.getElementById('projection-select');
    if (projectionSelect) {
        projectionSelect.addEventListener('change', function(e) {
            projectionState.currentProjection = e.target.value;
            drawMapProjection();
        });
    }
}


/**
 * Draw map with currently selected projection
 */
function drawMapProjection() {
    const ctx = projectionState.context;
    if (!ctx) return;
    
    // Clear canvas
    ctx.fillStyle = '#e3f2fd';
    ctx.fillRect(0, 0, projectionState.width, projectionState.height);
    
    // Draw graticule (lat/lon grid)
    drawGraticule();
    
    // Draw continents (simplified)
    drawContinents();
    
    // Draw ground track
    if (projectionState.groundTrackPoints.length > 0) {
        drawGroundTrack();
    }
    
    // Draw access windows
    if (projectionState.accessWindows.length > 0) {
        drawAccessWindows();
    }
    
    // Draw projection label
    ctx.fillStyle = '#333';
    ctx.font = '12px Arial';
    ctx.fillText(`Projection: ${projectionState.currentProjection.toUpperCase()}`, 10, 20);
}


/**
 * Draw latitude/longitude graticule
 */
function drawGraticule() {
    const ctx = projectionState.context;
    ctx.strokeStyle = '#ddd';
    ctx.lineWidth = 0.5;
    
    // Meridians (longitude lines)
    for (let lon = -180; lon <= 180; lon += 30) {
        ctx.beginPath();
        
        for (let lat = -90; lat <= 90; lat += 1) {
            const [x, y] = projectCoordinate(lat, lon);
            
            if (lat === -90) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }
        
        ctx.stroke();
    }
    
    // Parallels (latitude lines)
    for (let lat = -90; lat <= 90; lat += 30) {
        ctx.beginPath();
        
        for (let lon = -180; lon <= 180; lon += 1) {
            const [x, y] = projectCoordinate(lat, lon);
            
            if (lon === -180) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }
        
        ctx.stroke();
    }
}


/**
 * Draw simplified coastlines
 */
function drawContinents() {
    const ctx = projectionState.context;
    ctx.fillStyle = '#c8e6c9';
    ctx.strokeStyle = '#558b2f';
    ctx.lineWidth = 1;
    
    // Simplified continent rectangles (approximate positions)
    const continents = [
        // North America
        { lat: [25, 50], lon: [-125, -65] },
        // South America
        { lat: [-55, 12], lon: [-82, -35] },
        // Europe
        { lat: [35, 70], lon: [-10, 40] },
        // Africa
        { lat: [-35, 37], lon: [-18, 52] },
        // Asia
        { lat: [0, 75], lon: [40, 150] },
        // Australia
        { lat: [-45, -10], lon: [113, 154] }
    ];
    
    for (let continent of continents) {
        ctx.beginPath();
        
        const latMin = continent.lat[0];
        const latMax = continent.lat[1];
        const lonMin = continent.lon[0];
        const lonMax = continent.lon[1];
        
        // Draw as polygon of lat/lon grid points
        let isFirstPoint = true;
        
        for (let lat = latMin; lat <= latMax; lat += 5) {
            for (let lon = lonMin; lon <= lonMax; lon += 5) {
                const [x, y] = projectCoordinate(lat, lon);
                
                if (isFirstPoint) {
                    ctx.moveTo(x, y);
                    isFirstPoint = false;
                } else {
                    ctx.lineTo(x, y);
                }
            }
        }
        
        ctx.fill();
        ctx.stroke();
    }
}


/**
 * Project latitude/longitude to canvas coordinates
 * 
 * @param {number} lat - Latitude in degrees
 * @param {number} lon - Longitude in degrees
 * @returns {Array} [x, y] canvas coordinates
 */
function projectCoordinate(lat, lon) {
    const projection = projectionState.currentProjection;
    
    // Normalize inputs
    const lat_rad = lat * Math.PI / 180;
    const lon_rad = lon * Math.PI / 180;
    
    let x, y;
    
    switch (projection) {
        case 'sinusoidal':
            // Sinusoidal projection (equal-area)
            x = lon_rad * Math.cos(lat_rad);
            y = lat_rad;
            break;
            
        case 'mollweide':
            // Mollweide projection (equal-area, elliptical)
            // Simplified: use auxiliary angle iteration
            let theta = lat_rad;
            for (let i = 0; i < 5; i++) {
                theta = lat_rad + Math.asin(Math.sin(2 * theta) / 2);
            }
            x = 2 * lon_rad * Math.cos(theta) / Math.PI;
            y = Math.sin(theta);
            break;
            
        case 'equirectangular':
            // Equirectangular (simple cylindrical)
            x = lon_rad;
            y = lat_rad;
            break;
            
        case 'lambert_azimuthal':
            // Lambert Azimuthal Equal-Area (centered at North Pole)
            const k = Math.sqrt(2 / (1 + Math.sin(lat_rad) * Math.sin(lat_rad) + 
                                   Math.cos(lat_rad) * Math.cos(lat_rad) * Math.cos(lon_rad)));
            x = k * Math.cos(lat_rad) * Math.sin(lon_rad);
            y = -k * (Math.cos(lat_rad) * Math.cos(lon_rad) - Math.sin(lat_rad));
            break;
            
        default:
            x = lon_rad;
            y = lat_rad;
    }
    
    // Scale to canvas dimensions with padding
    const padding = 50;
    const mapWidth = projectionState.width - 2 * padding;
    const mapHeight = projectionState.height - 2 * padding;
    
    // Map [-π to π] x and [-π/2 to π/2] y to canvas
    const canvasX = padding + (x + Math.PI) / (2 * Math.PI) * mapWidth;
    const canvasY = padding + (Math.PI / 2 - y) / Math.PI * mapHeight;
    
    return [canvasX, canvasY];
}


/**
 * Add ground track point to map display
 * 
 * @param {number} latitude - Latitude in degrees
 * @param {number} longitude - Longitude in degrees
 */
function addGroundTrackPoint(latitude, longitude) {
    projectionState.groundTrackPoints.push({
        lat: latitude,
        lon: longitude
    });
}


/**
 * Draw ground track on map
 */
function drawGroundTrack() {
    const ctx = projectionState.context;
    ctx.strokeStyle = '#d32f2f';
    ctx.lineWidth = 2;
    ctx.fillStyle = '#d32f2f';
    
    if (projectionState.groundTrackPoints.length === 0) return;
    
    // Draw line
    ctx.beginPath();
    let isFirstPoint = true;
    
    for (let point of projectionState.groundTrackPoints) {
        const [x, y] = projectCoordinate(point.lat, point.lon);
        
        if (isFirstPoint) {
            ctx.moveTo(x, y);
            isFirstPoint = false;
        } else {
            ctx.lineTo(x, y);
        }
    }
    
    ctx.stroke();
    
    // Draw points as small circles
    for (let i = 0; i < projectionState.groundTrackPoints.length; i += Math.max(1, Math.floor(projectionState.groundTrackPoints.length / 50))) {
        const point = projectionState.groundTrackPoints[i];
        const [x, y] = projectCoordinate(point.lat, point.lon);
        
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, 2 * Math.PI);
        ctx.fill();
    }
}


/**
 * Add access window to map
 * 
 * @param {Object} window - Access window object {startLat, startLon, endLat, endLon}
 */
function addAccessWindow(window) {
    projectionState.accessWindows.push(window);
}


/**
 * Draw access windows on map
 */
function drawAccessWindows() {
    const ctx = projectionState.context;
    ctx.strokeStyle = '#00796b';
    ctx.lineWidth = 2;
    ctx.globalAlpha = 0.3;
    ctx.fillStyle = '#00796b';
    
    for (let accessWin of projectionState.accessWindows) {
        // Draw access window as circle/polygon around ground station
        const [stationX, stationY] = projectCoordinate(accessWin.station_lat, accessWin.station_lon);
        
        // Draw horizon circle (simplified)
        ctx.beginPath();
        ctx.arc(stationX, stationY, accessWin.radius_pixels || 50, 0, 2 * Math.PI);
        ctx.fill();
        ctx.stroke();
    }
    
    ctx.globalAlpha = 1.0;
}


/**
 * Clear all ground track and access window data
 */
function clearMapData() {
    projectionState.groundTrackPoints = [];
    projectionState.accessWindows = [];
    drawMapProjection();
}


/**
 * Request and display ground track on map
 * 
 * @param {Object} orbitParams - Orbital parameters
 */
async function requestGroundTrackMap(orbitParams) {
    const loadingDiv = document.getElementById('map-loading');
    if (loadingDiv) loadingDiv.style.display = 'block';
    
    try {
        // Use animation endpoint to get ground track
        const data = await apiCall('/animation/ground-track-trace', 'POST', {
            satellite_tle: orbitParams.tle,
            start_datetime: orbitParams.start_datetime || new Date().toISOString(),
            duration_minutes: orbitParams.duration_minutes || 120,
            step_seconds: orbitParams.step_seconds || 10
        });
        
        // Clear previous data
        clearMapData();
        
        // Add ground track points
        for (let frame of data.frames) {
            addGroundTrackPoint(frame.latitude_deg, frame.longitude_deg);
        }
        
        // Redraw map
        drawMapProjection();
        
        // Update info
        const infoDiv = document.getElementById('map-info');
        if (infoDiv) {
            infoDiv.innerHTML = `
                <p>Ground track points: ${data.frames.length}</p>
                <p>Duration: ${data.duration_minutes} minutes</p>
            `;
        }
        
    } catch (error) {
        console.error('Ground track map request failed:', error);
        alert('Failed to load ground track map');
    } finally {
        if (loadingDiv) loadingDiv.style.display = 'none';
    }
}


/**
 * Export current map as PNG
 */
function exportMapImage() {
    if (!projectionState.canvas) return;
    
    const link = document.createElement('a');
    link.href = projectionState.canvas.toDataURL('image/png');
    link.download = `ground-track-map-${projectionState.currentProjection}-${Date.now()}.png`;
    link.click();
}


/**
 * Export ground track data as GeoJSON
 */
function exportGroundTrackGeoJSON() {
    if (projectionState.groundTrackPoints.length === 0) {
        alert('No ground track points to export');
        return;
    }
    
    const geojson = {
        type: 'FeatureCollection',
        features: [
            {
                type: 'Feature',
                properties: {
                    name: 'Satellite Ground Track',
                    timestamp: new Date().toISOString()
                },
                geometry: {
                    type: 'LineString',
                    coordinates: projectionState.groundTrackPoints.map(p => [p.lon, p.lat])
                }
            }
        ]
    };
    
    const jsonStr = JSON.stringify(geojson, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `ground-track-${Date.now()}.geojson`;
    link.click();
    window.URL.revokeObjectURL(url);
}


/**
 * Toggle visibility of map elements
 */
function toggleMapElement(elementType) {
    switch (elementType) {
        case 'graticule':
            // Toggle graticule visibility
            break;
        case 'continents':
            // Toggle continents visibility
            break;
        case 'ground-track':
            projectionState.showGroundTrack = !projectionState.showGroundTrack;
            break;
        case 'access-windows':
            projectionState.showAccessWindows = !projectionState.showAccessWindows;
            break;
    }
    drawMapProjection();
}


/**
 * Get map statistics
 */
function getMapStatistics() {
    const stats = {
        ground_track_points: projectionState.groundTrackPoints.length,
        access_windows: projectionState.accessWindows.length,
        current_projection: projectionState.currentProjection,
        canvas_dimensions: {
            width: projectionState.width,
            height: projectionState.height
        }
    };
    
    if (projectionState.groundTrackPoints.length > 0) {
        const lats = projectionState.groundTrackPoints.map(p => p.lat);
        const lons = projectionState.groundTrackPoints.map(p => p.lon);
        
        stats.ground_track_bounds = {
            latitude_min: Math.min(...lats),
            latitude_max: Math.max(...lats),
            longitude_min: Math.min(...lons),
            longitude_max: Math.max(...lons)
        };
    }
    
    return stats;
}
