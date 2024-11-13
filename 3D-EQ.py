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

# HTML template with improvements
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>🌍 3D Earthquake Visualization</title>
    <!-- Include CesiumJS -->
    <script src="https://cesium.com/downloads/cesiumjs/releases/1.104/Build/Cesium/Cesium.js"></script>
    <!-- Include Heatmap.js -->
    <script src="https://cdn.jsdelivr.net/npm/heatmap.js/heatmap.min.js"></script>
    <link href="https://cesium.com/downloads/cesiumjs/releases/1.104/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
    <style>
        /* [CSS styles remain largely the same, ensuring proper layout and responsiveness] */
        html, body, #cesiumContainer {
            width: 100%; height: 100%; margin: 0; padding: 0; overflow: hidden;
            font-family: sans-serif;
        }
        #heatmapContainer {
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            pointer-events: none;
            z-index: 2;
            display: none;
        }
        /* Additional styling for UI components */
    </style>
</head>
<body>
    <div id="cesiumContainer"></div>
    <div id="heatmapContainer"></div>

    <!-- UI Components -->
    <div id="header">
        <h1>🌍 3D Earthquake Visualization</h1>
        <p>Explore recent earthquakes around the world in an interactive 3D map.</p>
        <div id="controls">
            <label for="dateRange">Date Range (Days): <span id="dateRangeValue">7</span></label>
            <input type="range" id="dateRange" min="1" max="30" value="7">
            <button id="toggleHeatmap">Enable Heatmap</button>
            <select id="basemapSelector">
                <option value="Bing Aerial">Bing Aerial</option>
                <option value="Bing Roads">Bing Roads</option>
                <option value="OpenStreetMap">OpenStreetMap</option>
            </select>
        </div>
    </div>

    <div id="earthquakeBar"></div>
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

    <div id="tooltip"></div>

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
            infoBox: false
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

        function getColor(magnitude) {
            if (magnitude >= 5.0) return Cesium.Color.RED.withAlpha(0.8);
            if (magnitude >= 4.0) return Cesium.Color.ORANGE.withAlpha(0.8);
            if (magnitude >= 3.0) return Cesium.Color.YELLOW.withAlpha(0.8);
            if (magnitude >= 2.0) return Cesium.Color.GREEN.withAlpha(0.8);
            return Cesium.Color.BLUE.withAlpha(0.8);
        }

        function fetchEarthquakes(days) {
            let feed = days <= 1 ? 'hour' : days <= 7 ? 'day' : 'month';
            const url = `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_${feed}.geojson`;

            fetch(url)
                .then(response => response.json())
                .then(data => {
                    earthquakes = data.features.sort((a, b) => (b.properties.mag || 0) - (a.properties.mag || 0));
                    updateEarthquakeData();
                })
                .catch(error => {
                    console.error('Error fetching earthquake data:', error);
                });
        }

        function updateEarthquakeData() {
            const top10 = earthquakes.slice(0, 10);
            const bar = document.getElementById('earthquakeBar');
            bar.innerHTML = '<div class="bar-item"><strong>Top Earthquakes:</strong></div>';

            top10.forEach(eq => {
                const mag = eq.properties.mag || 0;
                const place = eq.properties.place || 'Unknown';
                const div = document.createElement('div');
                div.className = 'bar-item';
                div.innerHTML = `<strong>${mag.toFixed(1)}</strong> - ${place}`;
                div.onclick = () => flyToEarthquake(eq);
                bar.appendChild(div);
            });

            const viewAll = document.createElement('div');
            viewAll.className = 'bar-item';
            viewAll.innerHTML = `<strong>View All</strong>`;
            viewAll.onclick = () => openModal(earthquakes);
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

            viewer.zoomTo(viewer.entities).otherwise(() => {
                console.log('Zoom failed');
            });
        }

        function addEarthquakePoints() {
            earthquakes.forEach(eq => {
                const [lon, lat, depth] = eq.geometry.coordinates;
                const mag = eq.properties.mag || 0;
                const depthKm = depth ? depth.toFixed(1) : 'Unknown';
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

        function generateHeatmap() {
            heatmapInstance.setData({ max: 10, data: [] });

            const heatData = earthquakes.map(eq => {
                const [lon, lat] = eq.geometry.coordinates;
                const mag = eq.properties.mag || 0;
                const cartesian = Cesium.Cartesian3.fromDegrees(lon, lat);
                const cartesian2 = Cesium.SceneTransforms.wgs84ToWindowCoordinates(viewer.scene, cartesian);
                if (cartesian2) {
                    return { x: cartesian2.x, y: cartesian2.y, value: mag };
                }
                return null;
            }).filter(point => point !== null);

            heatmapInstance.setData({
                max: 10,
                data: heatData
            });
        }

        function removeHeatmap() {
            heatmapInstance.setData({ max: 10, data: [] });
        }

        // Update heatmap on camera move
        viewer.scene.postRender.addEventListener(() => {
            if (heatmapEnabled) {
                generateHeatmap();
            }
        });

        document.getElementById('dateRange').oninput = function() {
            document.getElementById('dateRangeValue').innerText = this.value;
            fetchEarthquakes(parseInt(this.value));
        };

        document.getElementById('toggleHeatmap').onclick = function() {
            heatmapEnabled = !heatmapEnabled;
            updateEarthquakeData();
            this.innerText = heatmapEnabled ? 'Disable Heatmap' : 'Enable Heatmap';
        };

        // Basemap selector functionality
        document.getElementById('basemapSelector').onchange = function() {
            const selectedBasemap = this.value;
            if (viewer.baseLayer) {
                viewer.imageryLayers.remove(viewer.baseLayer);
            }
            switch(selectedBasemap) {
                case 'Bing Aerial':
                    viewer.baseLayer = viewer.imageryLayers.addImageryProvider(new Cesium.BingMapsImageryProvider({
                        url : 'https://dev.virtualearth.net',
                        mapStyle : Cesium.BingMapsStyle.AERIAL
                    }));
                    break;
                case 'Bing Roads':
                    viewer.baseLayer = viewer.imageryLayers.addImageryProvider(new Cesium.BingMapsImageryProvider({
                        url : 'https://dev.virtualearth.net',
                        mapStyle : Cesium.BingMapsStyle.ROAD
                    }));
                    break;
                case 'OpenStreetMap':
                    viewer.baseLayer = viewer.imageryLayers.addImageryProvider(new Cesium.OpenStreetMapImageryProvider({
                        url : 'https://a.tile.openstreetmap.org/'
                    }));
                    break;
                default:
                    viewer.baseLayer = viewer.imageryLayers.addImageryProvider(new Cesium.IonImageryProvider({ assetId: 2 }));
            }
        };

        function flyToEarthquake(eq) {
            const [lon, lat] = eq.geometry.coordinates;
            viewer.camera.flyTo({
                destination: Cesium.Cartesian3.fromDegrees(lon, lat, 200000),
                duration: 2,
                orientation: { pitch: Cesium.Math.toRadians(-30) }
            });
        }

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

        function updateTooltipPosition(position) {
            const x = position.x + 15;
            const y = position.y + 15;
            tooltip.style.left = x + 'px';
            tooltip.style.top = y + 'px';
        }

        const modal = document.getElementById('modal');
        document.getElementById('closeModal').onclick = () => modal.style.display = 'none';
        window.onclick = event => { if (event.target == modal) modal.style.display = 'none'; }

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
                            destination: Cesium.Cartesian3.fromDegrees(parseFloat(lon), parseFloat(lat), 80000),
                            duration: 2,
                            orientation: { pitch: Cesium.Math.toRadians(-30) }
                        });
                    }
                })
                .catch(error => {
                    console.error('Error searching location:', error);
                });
        }

        function openModal(earthquakes) {
            const tbody = document.querySelector('#fullEqTable tbody');
            tbody.innerHTML = earthquakes.map(eq => {
                const depth = eq.geometry.coordinates[2] ? eq.geometry.coordinates[2].toFixed(1) : 'Unknown';
                return `
                    <tr onclick='flyToEarthquake(${JSON.stringify(eq)})' style="cursor:pointer;">
                        <td>${(eq.properties.mag || 0).toFixed(1)}</td>
                        <td>${depth}</td>
                        <td>${eq.properties.place || 'Unknown'}</td>
                        <td>${new Date(eq.properties.time).toISOString().slice(0,19)} UTC</td>
                    </tr>
                `;
            }).join('');
            modal.style.display = 'block';
        }

        // Ensure flyToEarthquake is accessible globally
        window.flyToEarthquake = flyToEarthquake;

        // Fetch initial earthquake data
        fetchEarthquakes(7);

        // Add measurement tool (New Feature)
        // Users can measure distances between points on the map
        // [Additional code for measurement tool can be added here]

    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, cesium_token=CESIUM_ION_ACCESS_TOKEN)

if __name__ == '__main__':
    app.run(debug=True)
