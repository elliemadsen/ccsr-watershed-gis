// Catskills Watershed DEM Visualization with Three.js

let scene, camera, renderer, controls;
let terrainMesh;
let demData;
let cdlData;
let nlcdData;
let runoffData;
let precipTestData;
let nlcdClasses;
let cdlClasses;
let elevationScale = 1.0;
let showWireframe = false;
let dataLayer = 'elevation';
let samplingRate = 1;
let currentPrecipDataset = null;
let currentTimeIndex = 0;
let showCellBoundaries = false;
let precipDatasetRanges = {}; // Cache min/max for each dataset
let currentPrecipValues = null; // Cache current time step values
let cellBoundaryLines = null; // Three.js line object for cell boundaries
let compactClimateData = null; // Compact climate dataset (all 612 timesteps)
let climateCentroids = []; // Centroid positions in UTM coordinates
let compactClimateGlobalRange = { min: 0, max: 1 }; // Global min/max across all timesteps
let colorRangeMode = 'per-timestamp'; // 'per-timestamp' or 'global'
let visualizationMode = 'interpolated'; // 'interpolated' or 'grid-cells'
let gridBoundaryLines = null; // Three.js line object for climate grid boundaries
let selectedCategories = new Set(); // Track selected categories for CDL/NLCD

// Climate variable units mapping
const climateUnits = {
    'hurs': '%',
    'pr': 'kg m⁻² s⁻¹',
    'rlds': 'W m⁻²',
    'rsds': 'W m⁻²', 
    'sfcWind': 'm s⁻¹',
    'tasmax': 'K',
    'tasmin': 'K'
};

// Initialize
async function init() {
    try {
        // Load DEM data
        await loadDEMData();
        
        // Load CDL data
        await loadCDLData();
        
        // Load NLCD data
        await loadNLCDData();
        
        // Load Runoff data
        await loadRunoffData();
        
        // Load classification names
        await loadClassifications();
        
        // Setup Three.js scene
        setupScene();
        
        // Create terrain
        createTerrain();
        
        // Setup controls
        setupControls();
        
        // Update legend for initial state
        updateLegend();
        
        // Hide loading
        document.getElementById('loading').classList.add('hidden');
        
        // Start animation
        animate();
        
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('loading').innerHTML = `
            <div style="color: red;">Error: ${error.message}</div>
        `;
    }
}

// Load DEM data from JSON
async function loadDEMData() {
    const response = await fetch('web_data/dem_data.json');
    if (!response.ok) {
        throw new Error('Failed to load web_data/dem_data.json. Run prepare_dem.py first!');
    }
    demData = await response.json();
    console.log('DEM loaded:', demData.width, 'x', demData.height);
    console.log('Elevation range:', demData.elevation.min, '-', demData.elevation.max);
}

// Load CDL data from JSON
async function loadCDLData() {
    const response = await fetch('web_data/cdl_data.json');
    if (!response.ok) {
        throw new Error('Failed to load web_data/cdl_data.json. Run prepare_cdl.py first!');
    }
    cdlData = await response.json();
    console.log('CDL loaded:', cdlData.width, 'x', cdlData.height);
    console.log('CDL colormap entries:', Object.keys(cdlData.colormap).length);
}

// Load NLCD data from JSON
async function loadNLCDData() {
    const response = await fetch('web_data/nlcd_data.json');
    if (!response.ok) {
        throw new Error('Failed to load web_data/nlcd_data.json. Run prepare_nlcd.py first!');
    }
    nlcdData = await response.json();
    console.log('NLCD loaded:', nlcdData.width, 'x', nlcdData.height);
    console.log('NLCD colormap entries:', Object.keys(nlcdData.colormap).length);
}

// Load Runoff data from JSON
async function loadRunoffData() {
    const response = await fetch('web_data/runoff_data.json');
    if (!response.ok) {
        throw new Error('Failed to load web_data/runoff_data.json. Run prepare_runoff.py first!');
    }
    runoffData = await response.json();
    console.log('Runoff loaded:', runoffData.width, 'x', runoffData.height);
    console.log('Runoff range:', runoffData.range.min, '-', runoffData.range.max);
}

// Load classification names
async function loadClassifications() {
    const nlcdResponse = await fetch('../data/NLCD/nlcd_classes.json');
    if (nlcdResponse.ok) {
        nlcdClasses = await nlcdResponse.json();
        console.log('NLCD classes loaded:', Object.keys(nlcdClasses).length);
    }
    
    const cdlResponse = await fetch('../data/CDL/cdl_classes.json');
    if (cdlResponse.ok) {
        cdlClasses = await cdlResponse.json();
        console.log('CDL classes loaded:', Object.keys(cdlClasses).length);
    }
}

// Load compact climate data (all 612 timesteps, only 6 values each)
async function loadCompactPrecipData(filename) {
    try {
        const response = await fetch(filename);
        if (!response.ok) {
            console.warn(`Failed to load ${filename}: ${response.status}`);
            return;
        }
        compactClimateData = await response.json();
        
        // Convert lat/lon centroids to UTM (Zone 18N)
        // Very rough approximation for this region
        climateCentroids = compactClimateData.metadata.centroids.map(c => {
            const lat = c.lat;
            const lon = c.lon;
            // Rough UTM conversion for Zone 18N around 42°N
            const x = (lon + 75) * 85000 + 500000; // ~85km per degree longitude at this latitude
            const y = (lat - 40) * 111000 + 4400000; // ~111km per degree latitude
            return [x, y];
        });
        
        console.log('Compact climate loaded:', compactClimateData.timesteps.length, 'timesteps');
        console.log('Model:', compactClimateData.metadata.model);
        console.log('Variable:', compactClimateData.metadata.variable);
        
        // Calculate global min/max across all timesteps
        let globalMin = Infinity;
        let globalMax = -Infinity;
        for (const timestep of compactClimateData.timesteps) {
            if (timestep.values) {
                const stepMin = Math.min(...timestep.values);
                const stepMax = Math.max(...timestep.values);
                globalMin = Math.min(globalMin, stepMin);
                globalMax = Math.max(globalMax, stepMax);
            }
        }
        compactClimateGlobalRange = { min: globalMin, max: globalMax };
        console.log('Global range:', compactClimateGlobalRange.min.toExponential(3), '-', compactClimateGlobalRange.max.toExponential(3));
        
        // Set initial time to 0
        currentTimeIndex = 0;
    } catch (err) {
        console.error('Error loading compact precip data:', err);
    }
}

// Inverse Distance Weighting (IDW) interpolation from 6 centroids
function interpolateIDW(x, y, values) {
    let sumWeightedValues = 0;
    let sumWeights = 0;
    const power = 2; // IDW power parameter
    
    for (let i = 0; i < 6; i++) {
        const [cx, cy] = climateCentroids[i];
        const dx = x - cx;
        const dy = y - cy;
        const distSq = dx * dx + dy * dy;
        
        // Avoid division by zero if point is exactly on a centroid
        if (distSq < 1) {
            return values[i];
        }
        
        const weight = 1 / Math.pow(distSq, power / 2);
        sumWeightedValues += values[i] * weight;
        sumWeights += weight;
    }
    
    return sumWeightedValues / sumWeights;
}

// Create cell boundary lines in 3D space
function createCellBoundaryLines() {
    // Remove existing lines if any
    if (cellBoundaryLines) {
        scene.remove(cellBoundaryLines);
        cellBoundaryLines = null;
    }
    
    if (!precipTestData || !precipTestData.cellBoundaries || !demData || !scene) return;
    
    const material = new THREE.LineBasicMaterial({ color: 0xff0000 });
    const geometry = new THREE.BufferGeometry();
    const vertices = [];
    
    // Get scale factor for bounds
    const width = demData.width;
    const height = demData.height;
    const bounds = demData.bounds;
    const scaleX = (bounds.maxX - bounds.minX) / width;
    const scaleZ = (bounds.maxY - bounds.minY) / height;
    
    // Add each boundary segment
    precipTestData.cellBoundaries.forEach(boundary => {
        const [x1, y1] = boundary.start;
        const [x2, y2] = boundary.end;
        
        // Convert UTM to local coordinates (centered at 0,0)
        const localX1 = (x1 - bounds.minX) - (bounds.maxX - bounds.minX) / 2;
        const localZ1 = -((y1 - bounds.minY) - (bounds.maxY - bounds.minY) / 2);
        const localX2 = (x2 - bounds.minX) - (bounds.maxX - bounds.minX) / 2;
        const localZ2 = -((y2 - bounds.minY) - (bounds.maxY - bounds.minY) / 2);
        
        // Use a fixed elevation above terrain
        const fixedHeight = 500;
        
        // Add line segment
        vertices.push(localX1, fixedHeight, localZ1);
        vertices.push(localX2, fixedHeight, localZ2);
    });
    
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    cellBoundaryLines = new THREE.LineSegments(geometry, material);
    scene.add(cellBoundaryLines);
}

// Setup Three.js scene
function setupScene() {
    const container = document.getElementById('container');
    
    // Scene
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf5f5f5);
    
    // Camera
    camera = new THREE.PerspectiveCamera(
        60,
        window.innerWidth / window.innerHeight,
        1,
        100000
    );
    camera.position.set(0, 5000, 10000);
    
    // Renderer
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);
    
    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(1, 1, 1);
    scene.add(directionalLight);
    
    // Controls
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.enablePan = true; // Enable panning by default now
    
    // Handle resize
    window.addEventListener('resize', onWindowResize);
}

// Create terrain mesh from DEM
function createTerrain() {
    // Store current camera state if terrain already exists
    let savedCameraPosition = null;
    let savedCameraTarget = null;
    if (terrainMesh) {
        savedCameraPosition = camera.position.clone();
        savedCameraTarget = controls.target.clone();
    }
    
    const fullWidth = demData.width;
    const fullHeight = demData.height;
    
    // Apply sampling
    const width = Math.floor(fullWidth / samplingRate);
    const height = Math.floor(fullHeight / samplingRate);
    
    const { bounds, elevation } = demData;
    
    // Calculate real-world dimensions
    const worldWidth = bounds.maxX - bounds.minX;
    const worldHeight = bounds.maxY - bounds.minY;
    
    // Create geometry with exact vertex count matching data
    const geometry = new THREE.PlaneGeometry(
        worldWidth,
        worldHeight,
        width - 1,
        height - 1
    );
    
    // Adjust position to center at origin
    geometry.translate(0, 0, 0);
    
    // Set elevations and colors
    const positions = geometry.attributes.position.array;
    const colors = new Float32Array(positions.length);
    
    const elevRange = elevation.max - elevation.min;
    
    // Track which vertices are valid
    const validVertices = new Array(width * height).fill(false);
    
    // PlaneGeometry creates vertices from bottom-left, row by row
    // We need to map them correctly to our data array
    for (let i = 0; i < height; i++) {
        for (let j = 0; j < width; j++) {
            // PlaneGeometry vertex index
            const vertIdx = (i * width + j) * 3;
            const flatIdx = i * width + j;
            
            // Sample from full resolution data
            const fullI = Math.min(i * samplingRate, fullHeight - 1);
            const fullJ = Math.min(j * samplingRate, fullWidth - 1);
            
            // Get elevation from data
            let elev = demData.data[fullI][fullJ];
            
            // Skip invalid values (null)
            if (elev === null || isNaN(elev)) {
                // Set position way below the terrain so it's not visible
                positions[vertIdx + 2] = -10000;
                validVertices[flatIdx] = false;
                continue;
            }
            
            validVertices[flatIdx] = true;
            
            // Set Z position (elevation)
            positions[vertIdx + 2] = (elev - elevation.min) * elevationScale;
            
            // Set color based on data layer
            const normalized = (elev - elevation.min) / elevRange;
            const color = getColorForDataLayer(normalized, dataLayer, fullI, fullJ);
            colors[vertIdx] = color.r;
            colors[vertIdx + 1] = color.g;
            colors[vertIdx + 2] = color.b;
        }
    }
    
    // Remove faces (triangles) that contain invalid vertices
    const indices = geometry.index.array;
    const validIndices = [];
    
    for (let i = 0; i < indices.length; i += 3) {
        const v1 = indices[i];
        const v2 = indices[i + 1];
        const v3 = indices[i + 2];
        
        // Only keep triangle if all three vertices are valid
        if (validVertices[v1] && validVertices[v2] && validVertices[v3]) {
            validIndices.push(v1, v2, v3);
        }
    }
    
    // Update geometry with filtered indices
    geometry.setIndex(validIndices);
    
    console.log(`Terrain: ${width}x${height} (sampling 1 in ${samplingRate} pixels)`);
    console.log(`Kept ${validIndices.length / 3} triangles out of ${indices.length / 3}`);
    
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geometry.computeVertexNormals();
    
    // Create material
    const material = new THREE.MeshPhongMaterial({
        vertexColors: true,
        flatShading: false,
        wireframe: showWireframe,
        side: THREE.DoubleSide
    });
    
    // Create mesh
    if (terrainMesh) {
        scene.remove(terrainMesh);
    }
    
    terrainMesh = new THREE.Mesh(geometry, material);
    terrainMesh.rotation.x = -Math.PI / 2; // Rotate to horizontal
    scene.add(terrainMesh);
    
    // Restore camera state if it was saved, otherwise center on terrain
    if (savedCameraPosition && savedCameraTarget) {
        camera.position.copy(savedCameraPosition);
        controls.target.copy(savedCameraTarget);
    } else {
        controls.target.set(0, 0, 0);
    }
    controls.update();
}

// Get color based on data layer selection
function getColorForDataLayer(normalized, layer, row, col) {
    switch(layer) {
        case 'none':
            return { r: 0.7, g: 0.7, b: 0.7 }; // Light gray
        case 'elevation':
            // Black to white gradient (low to high)
            return { r: normalized, g: normalized, b: normalized };
        case 'cdl':
            // Get CDL value at this position
            if (cdlData && cdlData.data && row !== undefined && col !== undefined) {
                // Check if row and col are within bounds
                if (row < cdlData.height && col < cdlData.width) {
                    const cdlValue = cdlData.data[row][col];
                    if (cdlValue !== null && cdlValue !== undefined) {
                        // Check if this category is selected
                        if (selectedCategories.size === 0 || selectedCategories.has(cdlValue.toString())) {
                            const colorKey = cdlValue.toString();
                            if (cdlData.colormap && cdlData.colormap[colorKey]) {
                                const rgb = cdlData.colormap[colorKey];
                                return { r: rgb[0], g: rgb[1], b: rgb[2] };
                            }
                        }
                    }
                }
            }
            return { r: 0.8, g: 0.8, b: 0.8 }; // Gray for NoData or unselected
        case 'nlcd':
            // Get NLCD value at this position
            if (nlcdData && nlcdData.data && row !== undefined && col !== undefined) {
                if (row < nlcdData.height && col < nlcdData.width) {
                    const nlcdValue = nlcdData.data[row][col];
                    if (nlcdValue !== null && nlcdValue !== undefined) {
                        // Check if this category is selected
                        if (selectedCategories.size === 0 || selectedCategories.has(nlcdValue.toString())) {
                            const colorKey = nlcdValue.toString();
                            if (nlcdData.colormap && nlcdData.colormap[colorKey]) {
                                const rgb = nlcdData.colormap[colorKey];
                                return { r: rgb[0], g: rgb[1], b: rgb[2] };
                            }
                        }
                    }
                }
            }
            return { r: 0.8, g: 0.8, b: 0.8 }; // Gray for NoData or unselected
        case 'runoff':
            // Get runoff value at this position
            if (runoffData && runoffData.data && row !== undefined && col !== undefined) {
                if (row < runoffData.height && col < runoffData.width) {
                    const runoffValue = runoffData.data[row][col];
                    if (runoffValue !== null && runoffValue !== undefined) {
                        // Normalize to 0-1 range
                        const normalized = (runoffValue - runoffData.range.min) / 
                                         (runoffData.range.max - runoffData.range.min);
                        // Black to white gradient (same as elevation)
                        return { r: normalized, g: normalized, b: normalized };
                    }
                }
            }
            return { r: 0.8, g: 0.8, b: 0.8 }; // Gray for NoData
        case 'climate_precip':
        case 'climate_temp':
        case 'climate_humidity':
            // Real-time IDW interpolation or grid cells from compact data
            if (compactClimateData && climateCentroids.length === 6 && row !== undefined && col !== undefined) {
                // Get UTM coordinates for this pixel
                const x = demData.bounds.minX + (col / demData.width) * (demData.bounds.maxX - demData.bounds.minX);
                const y = demData.bounds.maxY - (row / demData.height) * (demData.bounds.maxY - demData.bounds.minY);
                
                // Get values for current timestep
                const timestep = compactClimateData.timesteps[currentTimeIndex];
                if (timestep && timestep.values) {
                    let value;
                    
                    if (visualizationMode === 'grid-cells') {
                        // Find nearest centroid for grid cell mode
                        let minDist = Infinity;
                        let nearestIdx = 0;
                        for (let i = 0; i < 6; i++) {
                            const [cx, cy] = climateCentroids[i];
                            const dist = Math.sqrt((x - cx) * (x - cx) + (y - cy) * (y - cy));
                            if (dist < minDist) {
                                minDist = dist;
                                nearestIdx = i;
                            }
                        }
                        value = timestep.values[nearestIdx];
                    } else {
                        // Interpolate value at this position using IDW
                        value = interpolateIDW(x, y, timestep.values);
                    }
                    
                    // Use global or per-timestep range based on user selection
                    let min, max;
                    if (colorRangeMode === 'global') {
                        min = compactClimateGlobalRange.min;
                        max = compactClimateGlobalRange.max;
                    } else {
                        min = Math.min(...timestep.values);
                        max = Math.max(...timestep.values);
                    }
                    
                    if (max > min) {
                        const normalized = (value - min) / (max - min);
                        // Black to white gradient
                        return { r: normalized, g: normalized, b: normalized };
                    }
                }
            }
            return { r: 0.5, g: 0.5, b: 0.5 }; // Medium gray for missing data
        default:
            return { r: 0.7, g: 0.7, b: 0.7 };
    }
}

// Get climate value at UTM coordinates
function getClimateValueAt(x, y) {
    if (!currentPrecipValues) return null;
    
    // Find nearest centroid (simplified - in production would use proper coordinate transformation)
    let minDist = Infinity;
    let nearestIdx = 0;
    
    for (let i = 0; i < precipitationData.centroids.length; i++) {
        const [lat, lon] = precipitationData.centroids[i];
        // Very rough approximation: 1 degree lat ~ 111km, 1 degree lon ~ 85km at this latitude
        const dx = (lon + 75) * 85000 - (x - 500000);  // Rough adjustment
        const dy = (lat - 42) * 111000 - (y - 4650000);  // Rough adjustment
        const dist = dx * dx + dy * dy;
        
        if (dist < minDist) {
            minDist = dist;
            nearestIdx = i;
        }
    }
    
    return currentPrecipValues[nearestIdx];
}

// Create cell boundary lines for climate data grid
function createGridBoundaryLines() {
    console.log('createGridBoundaryLines called');
    
    if (!compactClimateData || !demData) {
        console.log('Cannot create boundaries: missing data');
        return;
    }
    
    // Remove existing boundary lines
    if (gridBoundaryLines) {
        scene.remove(gridBoundaryLines);
        gridBoundaryLines = null;
    }
    
    const points = [];
    const material = new THREE.LineBasicMaterial({ color: 0xff0000, linewidth: 2 });
    
    // Get terrain dimensions in Three.js coordinates
    const worldWidth = demData.bounds.maxX - demData.bounds.minX;
    const worldHeight = demData.bounds.maxY - demData.bounds.minY;
    const y = 800; // High above terrain for visibility
    
    // Create 2x3 grid (2 rows, 3 columns)
    // Draw 1 horizontal line (divides 2 rows)
    const midZ = 0; // Center of terrain
    points.push(new THREE.Vector3(-worldWidth/2, y, midZ));
    points.push(new THREE.Vector3(worldWidth/2, y, midZ));
    
    // Draw 2 vertical lines (divides 3 columns)
    const col1X = -worldWidth/6; // 1/3 from left
    const col2X = worldWidth/6;  // 2/3 from left
    
    points.push(new THREE.Vector3(col1X, y, -worldHeight/2));
    points.push(new THREE.Vector3(col1X, y, worldHeight/2));
    
    points.push(new THREE.Vector3(col2X, y, -worldHeight/2));
    points.push(new THREE.Vector3(col2X, y, worldHeight/2));
    
    if (points.length > 0) {
        console.log(`Created ${points.length/2} boundary line segments`);
        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        gridBoundaryLines = new THREE.LineSegments(geometry, material);
        scene.add(gridBoundaryLines);
        console.log('Grid boundary lines added to scene');
    }
}

// Update legend based on current data layer
function updateLegend() {
    const legend = document.getElementById('legend');
    
    if (dataLayer === 'elevation') {
        legend.classList.add('visible');
        legend.innerHTML = `
            <h4>Elevation</h4>
            <div class="legend-gradient"></div>
            <div class="legend-labels">
                <span>${Math.round(demData.elevation.min)}m</span>
                <span>${Math.round(demData.elevation.max)}m</span>
            </div>
        `;
    } else if (dataLayer === 'runoff') {
        legend.classList.add('visible');
        legend.innerHTML = `
            <h4>Runoff Coefficient</h4>
            <div class="legend-gradient"></div>
            <div class="legend-labels">
                <span>${runoffData.range.min.toFixed(3)}</span>
                <span>${runoffData.range.max.toFixed(3)}</span>
            </div>
        `;
    } else if (dataLayer === 'nlcd' && nlcdClasses && nlcdData) {
        // Get unique values present in data
        const uniqueValues = new Set();
        for (let row of nlcdData.data) {
            for (let val of row) {
                if (val !== null) uniqueValues.add(val);
            }
        }
        
        legend.classList.add('visible');
        let html = '<h4>Land Cover (NLCD)</h4>';
        
        // Add category controls
        html += `
            <div class="category-controls">
                <div class="category-buttons">
                    <div class="category-btn" onclick="selectAllCategories('nlcd')">Select All</div>
                    <div class="category-btn" onclick="deselectAllCategories('nlcd')">Deselect All</div>
                </div>
            </div>
        `;
        
        html += '<div class="legend-categorical">';
        for (let value of Array.from(uniqueValues).sort((a, b) => a - b)) {
            const valueStr = value.toString();
            if (nlcdClasses[valueStr] && nlcdData.colormap[valueStr]) {
                const rgb = nlcdData.colormap[valueStr];
                const color = `rgb(${Math.round(rgb[0]*255)}, ${Math.round(rgb[1]*255)}, ${Math.round(rgb[2]*255)})`;
                const isSelected = selectedCategories.size === 0 || selectedCategories.has(valueStr);
                const disabledClass = isSelected ? '' : 'disabled';
                html += `
                    <div class="legend-item ${disabledClass}" onclick="toggleCategory('${valueStr}')">
                        <div class="legend-color" style="background: ${color}"></div>
                        <span class="legend-name">${nlcdClasses[valueStr]}</span>
                    </div>
                `;
            }
        }
        html += '</div>';
        legend.innerHTML = html;
    } else if (dataLayer === 'cdl' && cdlClasses && cdlData) {
        // Get unique values present in data
        const uniqueValues = new Set();
        for (let row of cdlData.data) {
            for (let val of row) {
                if (val !== null) uniqueValues.add(val);
            }
        }
        
        legend.classList.add('visible');
        let html = '<h4>Cropland Data Layer</h4>';
        
        // Add category controls
        html += `
            <div class="category-controls">
                <div class="category-buttons">
                    <div class="category-btn" onclick="selectAllCategories('cdl')">Select All</div>
                    <div class="category-btn" onclick="deselectAllCategories('cdl')">Deselect All</div>
                </div>
            </div>
        `;
        
        html += '<div class="legend-categorical">';
        for (let value of Array.from(uniqueValues).sort((a, b) => a - b)) {
            const valueStr = value.toString();
            if (cdlClasses[valueStr] && cdlData.colormap[valueStr]) {
                const rgb = cdlData.colormap[valueStr];
                const color = `rgb(${Math.round(rgb[0]*255)}, ${Math.round(rgb[1]*255)}, ${Math.round(rgb[2]*255)})`;
                const isSelected = selectedCategories.size === 0 || selectedCategories.has(valueStr);
                const disabledClass = isSelected ? '' : 'disabled';
                html += `
                    <div class="legend-item ${disabledClass}" onclick="toggleCategory('${valueStr}')">
                        <div class="legend-color" style="background: ${color}"></div>
                        <span class="legend-name">${cdlClasses[valueStr]}</span>
                    </div>
                `;
            }
        }
        html += '</div>';
        legend.innerHTML = html;
    } else if ((dataLayer === 'climate_precip' || dataLayer === 'climate_temp' || dataLayer === 'climate_humidity') && compactClimateData) {
        // Get range based on color range mode
        const timestep = compactClimateData.timesteps[currentTimeIndex];
        if (timestep && timestep.values) {
            let min, max;
            if (colorRangeMode === 'global') {
                min = compactClimateGlobalRange.min;
                max = compactClimateGlobalRange.max;
            } else {
                min = Math.min(...timestep.values);
                max = Math.max(...timestep.values);
            }
            
            // Get variable info based on current data layer and loaded data
            let variable, units;
            if (dataLayer === 'climate_precip') {
                variable = 'Precipitation';
                units = climateUnits[compactClimateData.metadata.variable] || 'mm/day';
            } else if (dataLayer === 'climate_temp') {
                variable = compactClimateData.metadata.label || 'Temperature';
                units = climateUnits[compactClimateData.metadata.variable] || 'K';
            } else if (dataLayer === 'climate_humidity') {
                variable = 'Relative Humidity';
                units = climateUnits[compactClimateData.metadata.variable] || '%';
            }
            
            legend.classList.add('visible');
            legend.innerHTML = `
                <h4>${variable}</h4>
                <div class="legend-gradient"></div>
                <div class="legend-labels">
                    <span>${min.toFixed(6)}</span>
                    <span>${max.toFixed(6)}</span>
                </div>
                <div style="text-align: center; font-size: 10px; color: #666; margin-top: 5px;">
                    ${units}
                </div>
            `;
        }
    } else {
        legend.classList.remove('visible');
    }
}

// Color scale for climate data (blue to red)
function climateColorScale(normalized) {
    // Blue (cold/low) to Red (hot/high)
    if (normalized < 0.5) {
        // Blue to white
        const t = normalized * 2;
        return { r: t, g: t, b: 1 };
    } else {
        // White to red
        const t = (normalized - 0.5) * 2;
        return { r: 1, g: 1 - t, b: 1 - t };
    }
}

//  Category management functions
function toggleCategory(categoryId) {
    if (selectedCategories.has(categoryId)) {
        selectedCategories.delete(categoryId);
    } else {
        selectedCategories.add(categoryId);
    }
    updateLegend();
    updateTerrain();
}

// Update time display without month abbreviations
function updateTimeDisplay() {
    const timeValue = document.getElementById('time-value');
    const timeDate = document.getElementById('time-date');
    
    if (compactClimateData && compactClimateData.timesteps[currentTimeIndex]) {
        const dateStr = compactClimateData.timesteps[currentTimeIndex].date;
        // Parse date carefully - use UTC to avoid timezone shifts
        const parts = dateStr.split('-');
        const year = parseInt(parts[0]);
        const month = parseInt(parts[1]); // 1-12
        
        // Map months to seasons (our seasonal data is March, June, Sept, Dec = months 3, 6, 9, 12)
        const seasonNames = {
            3: 'Spring',
            6: 'Summer',
            9: 'Fall',
            12: 'Winter'
        };
        
        if (timeValue) timeValue.textContent = `${year}-${String(month).padStart(2, '0')}`;
        if (timeDate) timeDate.textContent = `${seasonNames[month] || 'Month ' + month} ${year}`;
    }
}

// Category management functions
function toggleCategory(categoryId) {
    if (selectedCategories.has(categoryId)) {
        selectedCategories.delete(categoryId);
    } else {
        selectedCategories.add(categoryId);
    }
    updateLegend();
    updateTerrain();
}

function selectAllCategories(dataType) {
    selectedCategories.clear();
    updateLegend();
    updateTerrain();
}

function deselectAllCategories(dataType) {
    // Get all categories for the current data type
    if (dataType === 'nlcd' && nlcdData) {
        for (let row of nlcdData.data) {
            for (let val of row) {
                if (val !== null) selectedCategories.add(val.toString());
            }
        }
    } else if (dataType === 'cdl' && cdlData) {
        for (let row of cdlData.data) {
            for (let val of row) {
                if (val !== null) selectedCategories.add(val.toString());
            }
        }
    }
    // Now everything except what we want is selected, so invert by clearing all
    selectedCategories.clear();
    // Add just one invalid category so nothing shows
    selectedCategories.add('__none__');
    updateLegend();
    updateTerrain();
}

// Update terrain with new settings
function updateTerrain() {
    try {
        createTerrain();
        
        // Update grid boundaries if they should be shown
        if (showCellBoundaries && (dataLayer === 'climate_precip' || dataLayer === 'climate_temp' || dataLayer === 'climate_humidity')) {
            createGridBoundaryLines();
        } else if (gridBoundaryLines) {
            scene.remove(gridBoundaryLines);
            gridBoundaryLines = null;
        }
    } catch (err) {
        console.error('Error updating terrain:', err);
    }
}

// Setup UI controls
function setupControls() {
    // Data layer dropdown
    const layerSelect = document.getElementById('data-layer');
    const climatePanel = document.getElementById('climate-panel');
    const climatePanelTitle = document.getElementById('climate-panel-title');
    const climateModelSelect = document.getElementById('climate-model-select');
    
    // Model options for each climate type
    const climateModels = {
        climate_precip: {
            title: 'Climate Model: Precipitation',
            options: [
                { file: 'web_data/ACCESS-ESM1-5_pr_ssp370.json', label: 'ACCESS-ESM1-5' },
                { file: 'web_data/IPSL-CM6A-LR_pr_ssp370.json', label: 'IPSL-CM6A-LR' }
            ]
        },
        climate_temp: {
            title: 'Climate Model: Temperature',
            options: [
                { file: 'web_data/ACCESS-ESM1-5_tasmax_ssp370.json', label: 'ACCESS-ESM1-5 - Max Temp' },
                { file: 'web_data/ACCESS-ESM1-5_tasmin_ssp370.json', label: 'ACCESS-ESM1-5 - Min Temp' },
                { file: 'web_data/IPSL-CM6A-LR_tasmax_ssp370.json', label: 'IPSL-CM6A-LR - Max Temp' },
                { file: 'web_data/IPSL-CM6A-LR_tasmin_ssp370.json', label: 'IPSL-CM6A-LR - Min Temp' }
            ]
        },
        climate_humidity: {
            title: 'Climate Model: Humidity',
            options: [
                { file: 'web_data/ACCESS-ESM1-5_hurs_ssp370.json', label: 'ACCESS-ESM1-5' },
                { file: 'web_data/IPSL-CM6A-LR_hurs_ssp370.json', label: 'IPSL-CM6A-LR' }
            ]
        }
    };
    
    layerSelect.addEventListener('change', (e) => {
        dataLayer = e.target.value;
        
        // Reset categories when switching layers
        selectedCategories.clear();
        
        // Show/hide climate panel
        if (dataLayer.startsWith('climate_')) {
            const config = climateModels[dataLayer];
            climatePanelTitle.textContent = config.title;
            
            // Populate model dropdown
            climateModelSelect.innerHTML = config.options.map(opt => 
                `<option value="${opt.file}">${opt.label}</option>`
            ).join('');
            
            climatePanel.style.display = 'block';
            
            // Always load the initial dataset for the new climate type
            loadCompactPrecipData(climateModelSelect.value).then(() => {
                updateLegend();
                updateTerrain();
                updateTimeDisplay(); // Update time display after loading data
            });
        } else {
            climatePanel.style.display = 'none';
            updateLegend(); // Update legend for non-climate layers
            updateTerrain();
        }
    });
    
    // Climate model dropdown
    if (climateModelSelect) {
        climateModelSelect.addEventListener('change', async (e) => {
            const filename = e.target.value;
            await loadCompactPrecipData(filename);
            updateLegend(); // Update legend to reflect new model
            updateTerrain();
            updateTimeDisplay(); // Update time display when changing models
        });
    }
    
    // Timeline slider for compact climate data (in climate panel)
    const timeSlider = document.getElementById('time-slider');
    const timeValue = document.getElementById('time-value');
    const timeDate = document.getElementById('time-date');
    
    if (timeSlider) {
        timeSlider.addEventListener('input', (e) => {
            currentTimeIndex = parseInt(e.target.value);
            updateTimeDisplay();
            updateLegend();
            updateTerrain();
        });
    }
    
    // Cell boundaries checkbox (in climate panel)
    const boundariesCheckbox = document.getElementById('show-cell-boundaries');
    if (boundariesCheckbox) {
        boundariesCheckbox.addEventListener('change', (e) => {
            showCellBoundaries = e.target.checked;
            console.log('Boundaries checkbox changed:', showCellBoundaries);
            console.log('Current data layer:', dataLayer);
            
            if (showCellBoundaries && (dataLayer === 'climate_precip' || dataLayer === 'climate_temp' || dataLayer === 'climate_humidity')) {
                console.log('Attempting to create grid boundaries...');
                createGridBoundaryLines();
            } else if (gridBoundaryLines) {
                console.log('Removing grid boundaries...');
                scene.remove(gridBoundaryLines);
                gridBoundaryLines = null;
            }
        });
    }
    
    // Color range mode radio buttons (in climate panel)
    const colorRangeRadios = document.querySelectorAll('input[name="color-range"]');
    colorRangeRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (e.target.checked) {
                colorRangeMode = e.target.value;
                updateLegend();
                updateTerrain();
            }
        });
    });
    
    // Visualization mode radio buttons (in climate panel)
    const vizModeRadios = document.querySelectorAll('input[name="viz-mode"]');
    vizModeRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (e.target.checked) {
                visualizationMode = e.target.value;
                updateTerrain();
            }
        });
    });
    
    // Elevation scale slider
    const elevationSlider = document.getElementById('elevation-scale');
    const elevationValue = document.getElementById('elevation-value');
    
    elevationSlider.addEventListener('input', (e) => {
        elevationScale = parseFloat(e.target.value);
        elevationValue.textContent = elevationScale.toFixed(1);
        updateTerrain();
    });
    
    // Sampling slider
    const samplingSlider = document.getElementById('sampling-rate');
    const samplingValue = document.getElementById('sampling-value');
    
    samplingSlider.addEventListener('input', (e) => {
        samplingRate = parseInt(e.target.value);
        samplingValue.textContent = samplingRate;
        updateTerrain(); // Rebuild terrain with new sampling
    });
    
    // Wireframe checkbox
    const wireframeCheckbox = document.getElementById('wireframe');
    wireframeCheckbox.addEventListener('change', (e) => {
        showWireframe = e.target.checked;
        if (terrainMesh) {
            terrainMesh.material.wireframe = showWireframe;
        }
    });
    
    // Camera movement checkbox - toggles panning (moving camera target)
    const cameraCheckbox = document.getElementById('camera-movement');
    cameraCheckbox.addEventListener('change', (e) => {
        controls.enablePan = e.target.checked;
    });
}

// Animation loop
function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}

// Handle window resize
function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

// Toggle info modal
function toggleInfoModal() {
    const modal = document.getElementById('info-modal');
    modal.classList.toggle('show');
}

// Start
init().catch(err => {
    console.error('Failed to initialize:', err);
    const loading = document.getElementById('loading');
    loading.innerHTML = `<div style="color: red;">Failed to load: ${err.message}</div>`;
});
