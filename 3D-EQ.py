# 3D-EQ.py

import os
from flask import Flask, render_template_string

# Define Flask app
app = Flask(__name__)

# Retrieve the Cesium Ion Access Token from environment variables
CESIUM_ION_ACCESS_TOKEN = os.environ.get('CESIUM_ION_ACCESS_TOKEN')

# Ensure the Cesium Ion Access Token is available
if not CESIUM_ION_ACCESS_TOKEN:
    raise ValueError("CESIUM_ION_ACCESS_TOKEN environment variable is not set.")

# HTML template with fixes for date slider and heatmap toggle
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>🌍 3D Earthquake Visualization</title>
    <!-- Include CesiumJS -->
    <script src="https://cesium.com/downloads/cesiumjs/releases/1.104/Build/Cesium/Cesium.js"></script>
    <!-- Include Heatmap.js -->
    <script src="https://cdn.jsdelivr.net/npm/heatmap.js/build/heatmap.min.js"></script>
    <link href="https://cesium.com/downloads/cesiumjs/releases/1.104/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
    <style>
        html, body, #cesiumContainer {
            width: 100%; height: 100%; margin: 0; padding: 0; overflow: hidden;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
        }
        #heatmapContainer {
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            pointer-events: none;
            z-index: 2;
            display: none;
        }
        /* Header Styling */
        #header {
            position: absolute;
            top: 0; left: 0; width: 100%;
            background: rgba(255, 255, 255, 0.95);
            padding: 15px 30px;
            box-sizing: border-box;
            z-index: 3;
            display: flex;
            flex-direction: column;
            align-items: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        #header h1 {
            margin: 0;
            font-size: 24px;
            color: #333;
            text-align: center;
        }
        #header p {
            margin: 8px 0 15px 0;
            font-size: 14px;
            color: #666;
            text-align: center;
            max-width: 800px;
        }
        #controls {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            justify-content: center;
            align-items: center;
        }
        #controls label {
            font-size: 14px;
            color: #333;
        }
        /* Slider Styling */
        #dateRangeContainer {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        #dateRange {
            width: 200px;
        }
        #controls button, #controls select {
            padding: 6px 12px;
            font-size: 14px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            background-color: #0078D7;
            color: #fff;
            transition: background-color 0.3s;
        }
        #controls button:hover, #controls select:hover {
            background-color: #005a9e;
        }
        /* Legend Styling */
        #legend {
            margin-top: 15px;
            background: rgba(255,255,255,0.9);
            padding: 10px 15px;
            border-radius: 5px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
        }
        .legend-item {
            display: flex;
            align-items: center;
            margin-bottom: 5px;
        }
        .legend-color {
            width: 20px;
            height: 20px;
            margin-right: 8px;
            border-radius: 3px;
        }
        /* Earthquake Bar Styling */
        #earthquakeBar {
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            background: rgba(255, 255, 255, 0.95);
            padding: 10px 0;
            box-shadow: 0 -2px 4px rgba(0,0,0,0.1);
            z-index: 3;
            display: flex;
            overflow-x: auto;
            align-items: center;
        }
        #earthquakeBar::-webkit-scrollbar {
            height: 8px;
        }
        #earthquakeBar::-webkit-scrollbar-thumb {
            background: #ccc;
            border-radius: 4px;
        }
        .bar-item {
            flex: 0 0 auto;
            margin: 0 15px;
            font-size: 14px;
            color: #0078D7;
            cursor: pointer;
            transition: color 0.3s;
            white-space: nowrap;
        }
        .bar-item:hover {
            color: #005a9e;
            text-decoration: underline;
        }
        /* Modal Styling */
        #modal {
            display: none;
            position: fixed;
            z-index: 4;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(0,0,0,0.5);
        }
        #modalContent {
            background-color: #fff;
            margin: 5% auto;
            padding: 20px;
            border: 1px solid #888;
            width: 90%;
            max-width: 800px;
            border-radius: 5px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }
        #closeModal {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        #closeModal:hover,
        #closeModal:focus {
            color: #000;
            text-decoration: none;
        }
        /* Tooltip Styling */
        #tooltip {
            position: absolute;
            background: rgba(0, 0, 0, 0.8);
            color: #fff;
            padding: 8px 12px;
            border-radius: 4px;
            pointer-events: none;
            font-size: 13px;
            z-index: 5;
            display: none;
            max-width: 300px;
            word-wrap: break-word;
        }
        /* Search Box Styling */
        #searchBox {
            position: absolute;
            top: 15px;
            right: 30px;
            z-index: 4;
            display: flex;
            align-items: center;
            background: rgba(255, 255, 255, 0.95);
            padding: 5px;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        #searchInput {
            border: none;
            outline: none;
            padding: 5px;
            font-size: 14px;
        }
        #searchButton {
            border: none;
            background: none;
            cursor: pointer;
            font-size: 16px;
            padding: 5px;
        }
        /* Responsive Design */
        @media (max-width: 768px) {
            #header {
                padding: 10px 20px;
            }
            #header h1 {
                font-size: 20px;
            }
            #header p {
                font-size: 12px;
            }
            #controls {
                flex-direction: column;
                gap: 10px;
            }
            #controls label, #controls input[type=range], #controls button, #controls select {
                width: 100%;
                text-align: center;
            }
            #legend {
                flex-direction: column;
                gap: 8px;
            }
            #earthquakeBar {
                padding: 8px 0;
            }
            .bar-item {
                margin: 0 10px;
                font-size: 12px;
            }
            #searchBox {
                top: 10px;
                right: 20px;
            }
        }
    </style>
</head>
<body>
    <div id="cesiumContainer"></div>
    <div id="heatmapContainer"></div>

    <!-- Header with title, description, and controls -->
    <div id="header">
        <h1>🌍 3D Earthquake Visualization</h1>
        <p>Explore recent earthquakes around the world in an interactive 3D map.</p>
        <div id="controls">
            <div id="dateRangeContainer">
                <label for="dateRange">Date Range (Days): <span id="dateRangeValue">7</span></label>
                <input type="range" id="dateRange" min="1" max="30" value="7">
            </div>
            <button id="toggleHeatmap">Enable Heatmap</button>
            <select id="basemapSelector">
                <option value="Cesium World Imagery">Cesium World Imagery (Default)</option>
                <option value="OpenStreetMap">OpenStreetMap</option>
            </select>
        </div>
        <div id="legend">
            <div class="legend-item">
                <div class="legend-color" style="background-color: #d7191c;"></div>
                <span>Mag ≥ 5.0</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #fdae61;"></div>
                <span>4.0 ≤ Mag < 5.0</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #ffffbf;"></div>
                <span>3.0 ≤ Mag < 4.0</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #a6d96a;"></div>
                <span>2.0 ≤ Mag < 3.0</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #1a9641;"></div>
                <span>Mag < 2.0</span>
            </div>
        </div>
    </div>

    <!-- Earthquake bar -->
    <div id="earthquakeBar">
        <!-- Populated dynamically -->
    </div>

    <!-- Search box -->
    <div id="searchBox">
        <input type="text" id="searchInput" placeholder="Search location...">
        <button id="searchButton">🔍</button>
    </div>

    <!-- Tooltip -->
    <div id="tooltip"></div>

    <!-- Modal for viewing all earthquakes -->
    <div id="modal">
        <div id="modalContent">
            <span id="closeModal">&times;</span>
            <h2>All Earthquakes</h2>
            <table id="fullEqTable">
                <thead>
                    <tr>
                        <th>Mag</th>
                        <th>Depth (km)</th>
                        <th>Location</th>
                        <th>Time (UTC)</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>
    </div>

    <!-- Script Section -->
    <script>
        Cesium.Ion.defaultAccessToken = '{{ cesium_token }}';
        const viewer = new Cesium.Viewer('cesiumContainer', {
            terrainProvider: Cesium.createWorldTerrain(),
            baseLayerPicker: false,
            navigationHelpButton: true,
            sceneModePicker: true,
            animation: false,
            timeline: false,
            fullscreenButton: false,
            homeButton: true,
            geocoder: false,
            infoBox: false,
            selectionIndicator: false,
            navigationInstructionsInitiallyVisible: false
        });

        let heatmapEnabled = false;
        let earthquakes = [];

        // Initialize Heatmap.js
        const heatmapInstance = h337.create({
            container: document.getElementById('heatmapContainer'),
            radius: 15,
            maxOpacity: 0.6,
            minOpacity: 0,
            blur: 0.85,
            gradient: {
                0.0: 'blue',
                0.5: 'yellow',
                1.0: 'red'
            }
        });

        // Function to get color based on magnitude
        function getColor(magnitude) {
            if (magnitude >= 5.0) return Cesium.Color.fromCssColorString('#d7191c').withAlpha(0.8);
            if (magnitude >= 4.0) return Cesium.Color.fromCssColorString('#fdae61').withAlpha(0.8);
            if (magnitude >= 3.0) return Cesium.Color.fromCssColorString('#ffffbf').withAlpha(0.8);
            if (magnitude >= 2.0) return Cesium.Color.fromCssColorString('#a6d96a').withAlpha(0.8);
            return Cesium.Color.fromCssColorString('#1a9641').withAlpha(0.8);
        }

        // Fetch earthquakes from USGS API based on selected date range
        function fetchEarthquakes(days) {
            const endDate = new Date();
            const startDate = new Date();
            startDate.setDate(endDate.getDate() - days);
            const formatDate = date => date.toISOString().split('T')[0];

            const startTime = formatDate(startDate);
            const endTime = formatDate(endDate);
            const url = `https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=${startTime}&endtime=${endTime}`;

            fetch(url)
                .then(response => response.json())
                .then(data => {
                    if (!data.features) {
                        throw new Error("Invalid earthquake data format.");
                    }
                    earthquakes = data.features.sort((a, b) => (b.properties.mag || 0) - (a.properties.mag || 0));
                    updateEarthquakeData();
                });
        }

        // Update earthquake data on the map and top list
        function updateEarthquakeData() {
            const top10 = earthquakes.slice(0, 10);
            const bar = document.getElementById('earthquakeBar');
            bar.innerHTML = '<div class="bar-item"><strong>Top Earthquakes:</strong></div>';

            top10.forEach((eq, index) => {
                const mag = eq.properties.mag || 0;
                const place = eq.properties.place || 'Unknown';
                const div = document.createElement('div');
                div.className = 'bar-item';
                div.innerText = `⭐ ${mag.toFixed(1)} - ${place}`;
                div.onclick = () => flyToEarthquake(earthquakes.indexOf(eq));
                bar.appendChild(div);
            });

            const viewAll = document.createElement('div');
            viewAll.className = 'bar-item';
            viewAll.innerHTML = `<strong>View All</strong>`;
            viewAll.onclick = () => openModal();
            bar.appendChild(viewAll);

            // Remove existing entities
            viewer.entities.removeAll();

            if (heatmapEnabled) {
                generateHeatmap();
                document.getElementById('heatmapContainer').style.display = 'block';
            } else {
                removeHeatmap();
                addEarthquakePoints();
                document.getElementById('heatmapContainer').style.display = 'none';
                // Only zoom to entities if heatmap is disabled
                if (earthquakes.length > 0) {
                    viewer.zoomTo(viewer.entities).otherwise(() => {
                        console.log('Zoom failed');
                    });
                }
            }
        }

        // Add earthquake points to the Cesium viewer
        function addEarthquakePoints() {
            earthquakes.forEach(eq => {
                const [lon, lat, depth] = eq.geometry.coordinates;
                const mag = eq.properties.mag || 0;
                const depthKm = depth !== null && depth !== undefined ? depth.toFixed(1) : 'Unknown';
                viewer.entities.add({
                    position: Cesium.Cartesian3.fromDegrees(lon, lat),
                    point: {
                        pixelSize: 6 + mag * 2,
                        color: getColor(mag),
                        outlineColor: Cesium.Color.BLACK,
                        outlineWidth: 1
                    },
                    description: `
                        <b>Magnitude:</b> ${mag}<br>
                        <b>Depth:</b> ${depthKm} km<br>
                        <b>Location:</b> ${eq.properties.place}<br>
                        <b>Time:</b> ${new Date(eq.properties.time).toISOString().replace('T', ' ').split('.')[0]} UTC
                    `
                });
            });
        }

        // Generate heatmap data based on earthquake locations and magnitudes
        function generateHeatmap() {
            heatmapInstance.setData({ max: 10, data: [] });

            const heatData = earthquakes.map(eq => {
                const [lon, lat] = eq.geometry.coordinates;
                const mag = eq.properties.mag || 0;
                const cartesian = Cesium.Cartesian3.fromDegrees(lon, lat);
                const windowPosition = Cesium.SceneTransforms.wgs84ToWindowCoordinates(viewer.scene, cartesian);
                if (Cesium.defined(windowPosition)) {
                    return { x: windowPosition.x, y: windowPosition.y, value: mag };
                }
                return null;
            }).filter(point => point !== null);

            heatmapInstance.setData({
                max: 10,
                data: heatData
            });
        }

        // Remove heatmap data
        function removeHeatmap() {
            heatmapInstance.setData({ max: 10, data: [] });
        }

        // Update heatmap on camera move with debounce
        let heatmapTimeout;
        viewer.scene.postRender.addEventListener(() => {
            if (heatmapEnabled) {
                if (heatmapTimeout) clearTimeout(heatmapTimeout);
                heatmapTimeout = setTimeout(() => {
                    generateHeatmap();
                }, 500);
            }
        });

        // Fly to a specific earthquake location
        function flyToEarthquake(index) {
            const eq = earthquakes[index];
            if (!eq) {
                console.error('Invalid earthquake index:', index);
                return;
            }
            const [lon, lat] = eq.geometry.coordinates;
            viewer.camera.flyTo({
                destination: Cesium.Cartesian3.fromDegrees(lon, lat, 200000),
                duration: 2,
                orientation: { pitch: Cesium.Math.toRadians(270) }
            });
        }

        // Tooltip functionality
        const tooltip = document.getElementById('tooltip');
        const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);

        handler.setInputAction(movement => {
            const picked = viewer.scene.pick(movement.endPosition);
            if (Cesium.defined(picked) && picked.id && picked.id.description) {
                tooltip.style.display = 'block';
                tooltip.innerHTML = picked.id.description.getValue();
                updateTooltipPosition(movement.endPosition);
            } else {
                tooltip.style.display = 'none';
            }
        }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);

        handler.setInputAction(() => { tooltip.style.display = 'none'; }, Cesium.ScreenSpaceEventType.LEFT_DOWN);

        // Update tooltip position based on mouse movement
        function updateTooltipPosition(position) {
            const x = position.x + 15;
            const y = position.y + 15;
            tooltip.style.left = x + 'px';
            tooltip.style.top = y + 'px';
        }

        // Modal functionality for viewing all earthquakes
        const modal = document.getElementById('modal');
        document.getElementById('closeModal').onclick = () => modal.style.display = 'none';
        window.onclick = event => { if (event.target == modal) modal.style.display = 'none'; }

        // Search location functionality
        document.getElementById('searchButton').onclick = searchLocation;
        document.getElementById('searchInput').onkeydown = e => { if (e.key === 'Enter') searchLocation(); };

        function searchLocation() {
            const query = document.getElementById('searchInput').value.trim();
            if (!query) return;
            fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.length) {
                        const { lon, lat } = data[0];
                        viewer.camera.flyTo({
                            destination: Cesium.Cartesian3.fromDegrees(parseFloat(lon), parseFloat(lat), 400000),
                            duration: 2,
                            orientation: { pitch: Cesium.Math.toRadians(270) }
                        });
                    } else {
                        alert('Location not found.');
                    }
                })
                .catch(error => {
                    console.error('Error searching location:', error);
                });
        }

        // Open modal to display all earthquakes
        function openModal() {
            const tbody = document.querySelector('#fullEqTable tbody');
            if (!earthquakes.length) {
                tbody.innerHTML = '<tr><td colspan="4">No earthquake data available.</td></tr>';
                return;
            }
            tbody.innerHTML = earthquakes.map((eq, index) => {
                const depth = eq.geometry.coordinates[2] !== null && eq.geometry.coordinates[2] !== undefined ? eq.geometry.coordinates[2].toFixed(1) : 'Unknown';
                return `
                    <tr onclick='flyToEarthquake(${index})' style="cursor:pointer;">
                        <td>${(eq.properties.mag || 0).toFixed(1)}</td>
                        <td>${depth}</td>
                        <td>${eq.properties.place || 'Unknown'}</td>
                        <td>${new Date(eq.properties.time).toISOString().replace('T', ' ').split('.')[0]} UTC</td>
                    </tr>
                `;
            }).join('');
            modal.style.display = 'block';
        }

        // Ensure flyToEarthquake is accessible globally
        window.flyToEarthquake = flyToEarthquake;

        // Basemap selector functionality
        document.getElementById('basemapSelector').onchange = function() {
            const selectedBasemap = this.value;
            while (viewer.imageryLayers.length > 1) {
                viewer.imageryLayers.remove(viewer.imageryLayers.get(1));
            }
            switch(selectedBasemap) {
                case 'OpenStreetMap':
                    viewer.imageryLayers.addImageryProvider(new Cesium.OpenStreetMapImageryProvider({
                        url : 'https://a.tile.openstreetmap.org/'
                    }));
                    break;
                case 'Cesium World Imagery':
                default:
                    viewer.imageryLayers.addImageryProvider(new Cesium.IonImageryProvider({ assetId: 2 }));
            }
        };

        // Initialize the basemap selector to default
        document.getElementById('basemapSelector').value = 'Cesium World Imagery';

        // Event listeners for date range and heatmap toggle
        document.getElementById('dateRange').addEventListener('input', function() {
            const days = parseInt(this.value);
            document.getElementById('dateRangeValue').innerText = days;
            fetchEarthquakes(days);
        });

        document.getElementById('toggleHeatmap').addEventListener('click', function() {
            heatmapEnabled = !heatmapEnabled;
            this.innerText = heatmapEnabled ? 'Disable Heatmap' : 'Enable Heatmap';
            updateEarthquakeData();
        });

        // Fetch initial earthquake data
        fetchEarthquakes(7);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(
        HTML_TEMPLATE,
        cesium_token=CESIUM_ION_ACCESS_TOKEN
    )
