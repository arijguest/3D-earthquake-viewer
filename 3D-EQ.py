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
        /* [Styles remain the same] */
        html, body, #cesiumContainer {
            width: 100%; height: 100%; margin: 0; padding: 0; overflow: hidden;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
        }
        /* Other styles are unchanged */
    </style>
</head>
<body>
    <div id="cesiumContainer"></div>
    <div id="heatmapContainer"></div>

    <!-- Header with controls -->
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
        <!-- Legend and other components remain the same -->
    </div>

    <!-- Other HTML elements remain unchanged -->

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
                })
                .catch(error => {
                    console.error('Error fetching earthquake data:', error);
                    alert('Failed to load earthquake data. Please try again later.');
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
            }

            if (earthquakes.length > 0) {
                viewer.zoomTo(viewer.entities).otherwise(() => {
                    console.log('Zoom failed');
                });
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
                        <b>Time:</b> ${new Date(eq.properties.time).toISOString().slice(0,19)} UTC
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
                orientation: { pitch: Cesium.Math.toRadians(-30) }
            });
        }

        // Tooltip functionality remains the same

        // Modal functionality remains the same

        // Search location functionality remains the same

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
            document.getElementById('dateRangeValue').innerText = this.value;
            fetchEarthquakes(parseInt(this.value));
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
