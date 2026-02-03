// Catskills Watershed DEM Visualization with Three.js

let scene, camera, renderer, controls;
let terrainMesh;
let demData;
let cdlData;
let nlcdData;
let runoffData;
let elevationScale = 1.0;
let showWireframe = false;
let dataLayer = 'elevation';
let samplingRate = 1;

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
    const response = await fetch('dem_data.json');
    if (!response.ok) {
        throw new Error('Failed to load dem_data.json. Run prepare_dem.py first!');
    }
    demData = await response.json();
    console.log('DEM loaded:', demData.width, 'x', demData.height);
    console.log('Elevation range:', demData.elevation.min, '-', demData.elevation.max);
}

// Load CDL data from JSON
async function loadCDLData() {
    const response = await fetch('cdl_data.json');
    if (!response.ok) {
        throw new Error('Failed to load cdl_data.json. Run prepare_cdl.py first!');
    }
    cdlData = await response.json();
    console.log('CDL loaded:', cdlData.width, 'x', cdlData.height);
    console.log('CDL colormap entries:', Object.keys(cdlData.colormap).length);
}

// Load NLCD data from JSON
async function loadNLCDData() {
    const response = await fetch('nlcd_data.json');
    if (!response.ok) {
        throw new Error('Failed to load nlcd_data.json. Run prepare_nlcd.py first!');
    }
    nlcdData = await response.json();
    console.log('NLCD loaded:', nlcdData.width, 'x', nlcdData.height);
    console.log('NLCD colormap entries:', Object.keys(nlcdData.colormap).length);
}

// Load Runoff data from JSON
async function loadRunoffData() {
    const response = await fetch('runoff_data.json');
    if (!response.ok) {
        throw new Error('Failed to load runoff_data.json. Run prepare_runoff.py first!');
    }
    runoffData = await response.json();
    console.log('Runoff loaded:', runoffData.width, 'x', runoffData.height);
    console.log('Runoff range:', runoffData.range.min, '-', runoffData.range.max);
}

// Setup Three.js scene
function setupScene() {
    const container = document.getElementById('container');
    
    // Scene
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0xffffff);
    
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
    
    // Handle resize
    window.addEventListener('resize', onWindowResize);
}

// Create terrain mesh from DEM
function createTerrain() {
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
    
    // Center camera on terrain
    controls.target.set(0, 0, 0);
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
                        const colorKey = cdlValue.toString();
                        if (cdlData.colormap && cdlData.colormap[colorKey]) {
                            const rgb = cdlData.colormap[colorKey];
                            return { r: rgb[0], g: rgb[1], b: rgb[2] };
                        }
                    }
                }
            }
            return { r: 0.8, g: 0.8, b: 0.8 }; // Gray for NoData
        case 'nlcd':
            // Get NLCD value at this position
            if (nlcdData && nlcdData.data && row !== undefined && col !== undefined) {
                if (row < nlcdData.height && col < nlcdData.width) {
                    const nlcdValue = nlcdData.data[row][col];
                    if (nlcdValue !== null && nlcdValue !== undefined) {
                        const colorKey = nlcdValue.toString();
                        if (nlcdData.colormap && nlcdData.colormap[colorKey]) {
                            const rgb = nlcdData.colormap[colorKey];
                            return { r: rgb[0], g: rgb[1], b: rgb[2] };
                        }
                    }
                }
            }
            return { r: 0.8, g: 0.8, b: 0.8 }; // Gray for NoData
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
        default:
            return { r: 0.7, g: 0.7, b: 0.7 };
    }
}

// Update legend visibility and values
function updateLegend() {
    const legend = document.getElementById('legend');
    const legendTitle = document.querySelector('#legend h4');
    const legendMin = document.getElementById('legend-min');
    const legendMax = document.getElementById('legend-max');
    
    if (dataLayer === 'elevation') {
        legend.classList.add('visible');
        legendTitle.textContent = 'Elevation';
        legendMin.textContent = Math.round(demData.elevation.min) + 'm';
        legendMax.textContent = Math.round(demData.elevation.max) + 'm';
    } else if (dataLayer === 'runoff') {
        legend.classList.add('visible');
        legendTitle.textContent = 'Runoff Coefficient';
        legendMin.textContent = runoffData.range.min.toFixed(3);
        legendMax.textContent = runoffData.range.max.toFixed(3);
    } else {
        legend.classList.remove('visible');
    }
}

// Update terrain with new settings
function updateTerrain() {
    createTerrain();
    updateLegend();
}

// Setup UI controls
function setupControls() {
    // Data layer dropdown
    const layerSelect = document.getElementById('data-layer');
    layerSelect.addEventListener('change', (e) => {
        dataLayer = e.target.value;
        updateTerrain();
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

// Start
init();
