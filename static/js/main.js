document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Map if on Dashboard
    const mapContainer = document.getElementById('map');
    let map = null;
    let marker = null;
    let currentUserLat = null;
    let currentUserLng = null;
    let watchId = null;
    let activeAlertId = null;
    let isTracking = false;

    if (mapContainer) {
        // Automatically request location on load to populate the map
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    currentUserLat = position.coords.latitude;
                    currentUserLng = position.coords.longitude;
                    
                    // Remove loading text
                    mapContainer.innerHTML = '';
                    
                    // Initialize Leaflet Map
                    map = L.map('map').setView([currentUserLat, currentUserLng], 15);
                    
                    // Add OpenStreetMap tiles
                    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                        attribution: '&copy; OpenStreetMap contributors'
                    }).addTo(map);
                    
                    // Add marker
                    marker = L.marker([currentUserLat, currentUserLng]).addTo(map)
                        .bindPopup('Your Current Location').openPopup();
                },
                (error) => {
                    mapContainer.innerHTML = `<div class="map-loading" style="color:var(--primary);">Unable to retrieve location. Please enable GPS.</div>`;
                    console.error("Error obtaining location:", error);
                },
                { enableHighAccuracy: true }
            );
        } else {
            mapContainer.innerHTML = `<div class="map-loading" style="color:var(--primary);">Geolocation is not supported by your browser.</div>`;
        }
    }

    // 2. Handle SOS Button
    const sosBtn = document.getElementById('sosBtn');
    const sosStatus = document.getElementById('sosStatus');

    if (sosBtn) {
        sosBtn.addEventListener('click', () => {
            if (isTracking) {
                // Stop tracking
                isTracking = false;
                if (watchId) {
                    navigator.geolocation.clearWatch(watchId);
                    watchId = null;
                }
                sosBtn.querySelector('.sos-text').textContent = 'SOS';
                sosBtn.style.background = '';
                const pulse = sosBtn.querySelector('.pulse-ring');
                if(pulse) pulse.style.animationDuration = '2s';
                sosStatus.textContent = 'Tracking stopped. Refreshing...';
                setTimeout(() => window.location.reload(), 2000);
                return;
            }

            // UI Feedback
            sosBtn.style.transform = 'scale(0.95)';
            setTimeout(() => { sosBtn.style.transform = 'scale(1)'; }, 150);
            
            sosStatus.className = 'status-message';
            sosStatus.textContent = 'Getting precise location...';
            sosStatus.classList.remove('hidden');

            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        const lat = position.coords.latitude;
                        const lng = position.coords.longitude;
                        
                        // Update map if it exists
                        if (map && marker) {
                            marker.setLatLng([lat, lng]);
                            map.setView([lat, lng], 15);
                        }
                        
                        // Send data to backend
                        sendSOSAlert(lat, lng);
                    },
                    (error) => {
                        // Fallback if location fails but user needs to send alert anyway
                        console.warn("Location failed, sending SOS without coordinates.", error);
                        sendSOSAlert(null, null);
                    },
                    { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
                );
            } else {
                sendSOSAlert(null, null);
            }
        });
    }

    function sendSOSAlert(lat, lng) {
        sosStatus.textContent = 'Sending alerts to trusted contacts...';
        
        fetch('/api/sos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ latitude: lat, longitude: lng })
        })
        .then(response => response.json())
        .then(data => {
            if(data.status === 'success') {
                sosStatus.textContent = data.message;
                // Add a pulse animation to button to indicate active state
                const pulse = sosBtn.querySelector('.pulse-ring');
                if(pulse) pulse.style.animationDuration = '0.5s';
                
                sosBtn.querySelector('.sos-text').textContent = 'STOP';
                sosBtn.style.background = '#ff9f43'; // Warning color
                
                activeAlertId = data.alert_id;
                isTracking = true;
                
                // Start continuous tracking
                if (navigator.geolocation) {
                    watchId = navigator.geolocation.watchPosition(
                        (pos) => {
                            const newLat = pos.coords.latitude;
                            const newLng = pos.coords.longitude;
                            
                            // Update map marker
                            if (map && marker) {
                                marker.setLatLng([newLat, newLng]);
                                map.setView([newLat, newLng]);
                            }
                            
                            // Send update to server
                            fetch('/api/sos/update', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    alert_id: activeAlertId,
                                    latitude: newLat,
                                    longitude: newLng
                                })
                            }).catch(e => console.error("Update failed", e));
                        },
                        (err) => console.error("WatchPosition error:", err),
                        { enableHighAccuracy: true, maximumAge: 0 }
                    );
                }
            } else {
                throw new Error(data.message || 'Unknown error');
            }
        })
        .catch(error => {
            sosStatus.className = 'status-message error';
            sosStatus.textContent = 'Failed to send alert. Try calling emergency services directly.';
            console.error('Error:', error);
        });
    }

    // 3. Auto-hide flash messages
    const flashMessages = document.querySelectorAll('.alert');
    if (flashMessages.length > 0) {
        setTimeout(() => {
            flashMessages.forEach(msg => {
                msg.style.opacity = '0';
                setTimeout(() => msg.remove(), 300);
            });
        }, 5000);
    }
});
