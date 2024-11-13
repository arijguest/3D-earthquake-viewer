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

# HTML template with updated heatmap functionality
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>🌍 3D Earthquake Visualization</title>
    <!-- Include CesiumJS -->
    <script src="https://cesium.com/downloads/cesiumjs/releases/1.104/Build/Cesium/Cesium.js"></script>
    <link href="https://cesium.com/downloads/cesiumjs/releases/1.104/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
    <style>
        /* (Styles remain unchanged) */
    </style>
</head>
<body>
    <div id="cesiumContainer"></div>

    <!-- Header with title, description, and controls -->
    <div id="header">
        <!-- (Header content remains unchanged) -->
    </div>

    <!-- Earthquake bar -->
    <div id="earthquakeBar">
        <!-- Populated dynamically -->
    </div>

    <!-- Search box -->
    <div id="searchBox">
        <!-- (Search box remains unchanged) -->
    </div>

    <!-- Tooltip -->
    <div id="tooltip"></div>

    <!-- Modal for viewing all earthquakes -->
    <div id="modal">
        <!-- (Modal content remains unchanged) -->
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
        let heatmapDataSource;

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

            // Remove existing entities and heatmap
            viewer.entities.removeAll();
            if (heatmapDataSource) {
                viewer.dataSources.remove(heatmapDataSource);
                heatmapDataSource = null;
            }

            if (heatmapEnabled) {
                addHeatmap();
                document.getElementById('heatmapContainer').style.display = 'block';
            } else {
                addEarthquakePoints();
                document.getElementById('heatmapContainer').style.display = 'none';
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

        // Add heatmap using Cesium's PointPrimitiveCollection
        function addHeatmap() {
            heatmapDataSource = new Cesium.CustomDataSource('heatmap');
            viewer.dataSources.add(heatmapDataSource);

            const points = earthquakes.map(eq => {
                const [lon, lat] = eq.geometry.coordinates;
                const mag = eq.properties.mag || 0;
                return {
                    position: Cesium.Cartesian3.fromDegrees(lon, lat),
                    color: Cesium.Color.RED.withAlpha(0.5),
                    pixelSize: mag * 2
                };
            });

            heatmapDataSource.entities.add({
                name: 'Heatmap',
                position: Cesium.Cartesian3.fromDegrees(0,0),
                point: {
                    pixelSize: 1,
                    color: Cesium.Color.TRANSPARENT,
                    outlineWidth: 0
                }
            });

            points.forEach(point => {
                heatmapDataSource.entities.add({
                    position: point.position,
                    point: {
                        pixelSize: point.pixelSize,
                        color: Cesium.Color.RED.withAlpha(0.5)
                    }
                });
            });
        }

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
                            destination: Cesium.Cartesian3.fromDegrees(parseFloat(lon), parseFloat(lat), 2000000),
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
