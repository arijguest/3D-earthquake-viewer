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

# HTML template with enhancements
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>🌍 3D Earthquake Visualization</title>
    <script src="https://cesium.com/downloads/cesiumjs/releases/1.104/Build/Cesium/Cesium.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/heatmap.js/2.0.5/heatmap.min.js"></script>
    <link href="https://cesium.com/downloads/cesiumjs/releases/1.104/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
    <style>
        html, body, #cesiumContainer {
            width: 100%; height: 100%; margin: 0; padding: 0; overflow: hidden;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
        }
        #header {
            position: absolute;
            top: 0; left: 0; width: 100%;
            background: rgba(255, 255, 255, 0.95);
            padding: 15px 30px;
            box-sizing: border-box;
            z-index: 2;
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
        #controls input[type=range] {
            width: 200px;
        }
        #controls button {
            padding: 6px 12px;
            font-size: 14px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            background-color: #0078D7;
            color: #fff;
            transition: background-color 0.3s;
        }
        #controls button:hover {
            background-color: #005a9e;
        }
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
        #earthquakeBar {
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            background: rgba(255, 255, 255, 0.95);
            padding: 10px 0;
            box-shadow: 0 -2px 4px rgba(0,0,0,0.1);
            z-index: 2;
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
        #modal {
            display: none;
            position: fixed;
            z-index: 3;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(0,0,0,0.5);
        }
        #modalContent {
            background-color: #fff;
            margin: 10% auto;
            padding: 20px;
            border: 1px solid #888;
            width: 80%;
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
        #zoomControls {
            position: absolute;
            top: 60px;
            right: 30px;
            z-index: 4;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .zoom-button {
            width: 40px;
            height: 40px;
            background-color: rgba(255, 255, 255, 0.8);
            border: 1px solid #ccc;
            border-radius: 4px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            transition: background-color 0.3s;
        }
        .zoom-button:hover {
            background-color: rgba(255, 255, 255, 1);
        }
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
        @media (max-width: 1024px) {
            #sidebar {
                width: 280px;
            }
        }
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
            #controls label, #controls input[type=range], #controls button {
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
            #zoomControls {
                top: 50px;
                right: 20px;
            }
        }
    </style>
</head>
<body>
    <div id="header">
        <h1>🌍 3D Earthquake Visualization</h1>
        <p>Interactive 3D map displaying recent earthquakes around the world. Explore seismic activity with detailed information and visual representations.</p>
        <div id="controls">
            <label for="dateRange">Date Range (Days): <span id="dateRangeValue">7</span></label>
            <input type="range" id="dateRange" min="1" max="30" value="7">
            <button id="toggleHeatmap">Enable Heatmap</button>
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

    <div id="cesiumContainer"></div>

    <div id="earthquakeBar">
        <div class="bar-item"><strong>Top Earthquakes:</strong></div>
        <div class="bar-item" id="viewAllButton"><strong>View All</strong></div>
    </div>

    <div id="modal">
        <div id="modalContent">
            <span id="closeModal">&times;</span>
            <h2>All Earthquakes</h2>
            <table id="fullEqTable">
                <thead>
                    <tr>
                        <th>Mag</th>
                        <th>Location</th>
                        <th>Time (UTC)</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>
    </div>

    <div id="tooltip"></div>

    <div id="zoomControls">
        <div class="zoom-button" id="zoomIn">+</div>
        <div class="zoom-button" id="zoomOut">−</div>
    </div>

    <div id="searchBox">
        <input type="text" id="searchInput" placeholder="Search location...">
        <button id="searchButton">🔍</button>
    </div>

    <script>
        Cesium.Ion.defaultAccessToken = '{{ cesium_token }}';
        const viewer = new Cesium.Viewer('cesiumContainer', {
            terrainProvider: Cesium.createWorldTerrain(),
            animation: false,
            timeline: false,
            baseLayerPicker: false,
            geocoder: false,
            homeButton: false,
            infoBox: false,
            sceneModePicker: false,
            fullscreenButton: false,
            navigationHelpButton: false,
            shouldAnimate: true
        });

        viewer.scene.screenSpaceCameraController.enableZoom = true;
        viewer.scene.screenSpaceCameraController.enableLook = true;
        viewer.scene.screenSpaceCameraController.enableTilt = true;
        viewer.scene.screenSpaceCameraController.enableRotate = true;

        viewer.scene.screenSpaceCameraController.minimumZoomDistance = 1000;
        viewer.scene.screenSpaceCameraController.maximumZoomDistance = 20000000;

        let heatmap = false;
        let heatmapInstance;

        function getColor(magnitude) {
            if (magnitude >= 5.0) return Cesium.Color.fromCssColorString('#d7191c').withAlpha(0.8);
            if (magnitude >= 4.0) return Cesium.Color.fromCssColorString('#fdae61').withAlpha(0.8);
            if (magnitude >= 3.0) return Cesium.Color.fromCssColorString('#ffffbf').withAlpha(0.8);
            if (magnitude >= 2.0) return Cesium.Color.fromCssColorString('#a6d96a').withAlpha(0.8);
            return Cesium.Color.fromCssColorString('#1a9641').withAlpha(0.8);
        }

        function fetchEarthquakes(days) {
            let feed = days <= 1 ? 'hour' : days <= 7 ? 'day' : 'month';
            const url = `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_${feed}.geojson`;

            fetch(url)
                .then(response => response.json())
                .then(data => {
                    const earthquakes = data.features.sort((a, b) => (b.properties.mag || 0) - (a.properties.mag || 0));
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

                    viewer.entities.removeAll();
                    if (heatmap) {
                        heatmapInstance.setData({ max: 5.0, data: [] });
                    }

                    const heatmapData = [];

                    earthquakes.forEach(eq => {
                        const [lon, lat] = eq.geometry.coordinates;
                        const mag = eq.properties.mag || 0;
                        viewer.entities.add({
                            position: Cesium.Cartesian3.fromDegrees(lon, lat, 0),
                            point: {
                                pixelSize: 6 + mag * 2,
                                color: getColor(mag),
                                outlineColor: Cesium.Color.BLACK,
                                outlineWidth: 1
                            },
                            description: `
                                <b>Magnitude:</b> ${mag}<br>
                                <b>Location:</b> ${eq.properties.place}<br>
                                <b>Time:</b> ${new Date(eq.properties.time).toISOString().slice(0,19)} UTC
                            `
                        });
                        heatmapData.push({ x: lon, y: lat, value: mag });
                    });

                    if (heatmap) {
                        heatmapInstance.setData({ max: 5.0, data: heatmapData.map(d => ({ x: d.x, y: d.y, value: d.value })) });
                    }

                    viewer.zoomTo(viewer.entities);
                })
                .catch(console.error);
        }

        fetchEarthquakes(7);

        document.getElementById('dateRange').oninput = function() {
            document.getElementById('dateRangeValue').innerText = this.value;
            fetchEarthquakes(parseInt(this.value));
        };

        document.getElementById('toggleHeatmap').onclick = function() {
            heatmap = !heatmap;
            if (heatmap) {
                heatmapInstance = h337.create({
                    container: document.getElementById('cesiumContainer'),
                    radius: 40,
                    maxOpacity: 0.6,
                    minOpacity: 0,
                    blur: 0.75,
                    gradient: {
                        0.0: 'blue',
                        0.5: 'lime',
                        0.7: 'yellow',
                        1.0: 'red'
                    }
                });
                fetchEarthquakes(parseInt(document.getElementById('dateRange').value));
                this.innerText = 'Disable Heatmap';
            } else {
                heatmapInstance.remove();
                heatmapInstance = null;
                fetchEarthquakes(parseInt(document.getElementById('dateRange').value));
                this.innerText = 'Enable Heatmap';
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
                const rect = viewer.canvas.getBoundingClientRect();
                let x = movement.endPosition.x + rect.left + 15;
                let y = movement.endPosition.y + rect.top + 15;
                x = Math.min(x, window.innerWidth - 320);
                y = Math.min(y, window.innerHeight - 120);
                tooltip.style.left = x + 'px';
                tooltip.style.top = y + 'px';
            } else {
                tooltip.style.display = 'none';
            }
        }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);

        handler.setInputAction(() => { tooltip.style.display = 'none'; }, Cesium.ScreenSpaceEventType.LEFT_DOWN);

        const modal = document.getElementById('modal');
        document.getElementById('closeModal').onclick = () => modal.style.display = 'none';
        window.onclick = event => { if (event.target == modal) modal.style.display = 'none'; }

        document.getElementById('zoomIn').onclick = () => viewer.camera.zoomIn(10000);
        document.getElementById('zoomOut').onclick = () => viewer.camera.zoomOut(10000);

        document.getElementById('searchButton').onclick = searchLocation;
        document.getElementById('searchInput').onkeydown = e => { if (e.key === 'Enter') searchLocation(); };

        function searchLocation() {
            const query = document.getElementById('searchInput').value.trim();
            if (!query) return;
            fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.length) {
                        const { lon, lat, boundingbox } = data[0];
                        let height = 20000;
                        if (boundingbox) {
                            const [south, north, west, east] = boundingbox.map(Number);
                            const maxDiff = Math.max(north - south, east - west);
                            height = Math.min(Math.max(20000 / maxDiff, 10000), 80000);
                        }
                        viewer.camera.flyTo({
                            destination: Cesium.Cartesian3.fromDegrees(parseFloat(lon), parseFloat(lat), height),
                            duration: 2,
                            orientation: { pitch: Cesium.Math.toRadians(-30) }
                        });
                    } else {
                        alert('Location not found.');
                    }
                })
                .catch(console.error);
        }

        function openModal(earthquakes) {
            const tbody = document.querySelector('#fullEqTable tbody');
            tbody.innerHTML = earthquakes.map(eq => `
                <tr onclick="flyToEarthquake(${JSON.stringify(eq)})">
                    <td>${(eq.properties.mag || 0).toFixed(1)}</td>
                    <td>${eq.properties.place || 'Unknown'}</td>
                    <td>${new Date(eq.properties.time).toISOString().slice(0,19)} UTC</td>
                </tr>
            `).join('');
            modal.style.display = 'block';
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, cesium_token=CESIUM_ION_ACCESS_TOKEN)

