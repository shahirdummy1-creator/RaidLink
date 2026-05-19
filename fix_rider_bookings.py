import re

with open('templates/rider_bookings.html', 'r', encoding='utf-8') as f:
    content = f.read()

# ── 1. Replace driver location HTML block ──────────────────────────────────
new_block = """{% if b.accepted_by %}
                <!-- Driver Location -->
                <div id="driver-loc-{{ b.id }}" style="padding:14px 20px;border-top:1px solid #f3f4f6;">
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
                        <div style="font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#6b7280;">
                            <i class="bi bi-geo-alt-fill text-primary me-1"></i> Driver Location
                        </div>
                        <a id="track-btn-{{ b.id }}" href="#" target="_blank"
                           style="display:none;align-items:center;gap:5px;background:#0d6efd;color:#fff;padding:5px 12px;border-radius:8px;font-size:.75rem;font-weight:600;text-decoration:none;">
                            <i class="bi bi-broadcast"></i> Live Track
                        </a>
                    </div>
                    <div id="driver-stats-{{ b.id }}" style="display:none;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px;">
                        <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:8px 12px;text-align:center;">
                            <div style="font-size:.62rem;font-weight:700;text-transform:uppercase;color:#6b7280;">Distance Away</div>
                            <div id="driver-dist-val-{{ b.id }}" style="font-size:1.1rem;font-weight:800;color:#1d4ed8;">&#8212;</div>
                        </div>
                        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:8px 12px;text-align:center;">
                            <div style="font-size:.62rem;font-weight:700;text-transform:uppercase;color:#6b7280;">ETA to Pickup</div>
                            <div id="driver-eta-val-{{ b.id }}" style="font-size:1.1rem;font-weight:800;color:#059669;">&#8212;</div>
                        </div>
                    </div>
                    <div id="driver-map-{{ b.id }}" style="width:100%;height:200px;border-radius:10px;background:#f3f4f6;display:flex;align-items:center;justify-content:center;">
                        <span style="color:#9ca3af;font-size:.82rem;"><i class="bi bi-arrow-clockwise me-1"></i>Fetching driver location&#8230;</span>
                    </div>
                </div>
                {% endif %}"""

content = re.sub(
    r'\{% if b\.accepted_by %\}\s*<!-- Driver Location -->.*?\{% endif %\}',
    new_block, content, flags=re.DOTALL
)

# ── 2. Replace JS section ──────────────────────────────────────────────────
new_js = """// ── Driver location tracking ──────────────────────────────────────────────
const DRIVER_BOOKINGS = [
    {% for b in confirmed %}{% if b.accepted_by %}
    { id: {{ b.id }}, driver: '{{ b.accepted_by }}', pickup_lat: {{ b.pickup_lat or 'null' }}, pickup_lng: {{ b.pickup_lng or 'null' }} },
    {% endif %}{% endfor %}
];

const driverMaps    = {};   // bookingId -> google.maps.Map
const driverMarkers = {};   // bookingId -> google.maps.Marker

function initDriverMaps() {
    // Called once Google Maps JS is ready
    DRIVER_BOOKINGS.forEach(b => {
        const el = document.getElementById(`driver-map-${b.id}`);
        if (!el) return;
        const map = new google.maps.Map(el, {
            zoom: 14,
            center: { lat: 11.0168, lng: 76.9558 },   // default Coimbatore
            disableDefaultUI: true,
            zoomControl: true,
            gestureHandling: 'cooperative'
        });
        driverMaps[b.id] = map;
        driverMarkers[b.id] = new google.maps.Marker({
            map,
            icon: {
                url: 'https://maps.google.com/mapfiles/ms/icons/cabs/taxi.png',
                scaledSize: new google.maps.Size(40, 40)
            },
            title: 'Driver'
        });
        // Also add pickup marker if coords available
        if (b.pickup_lat) {
            new google.maps.Marker({
                map,
                position: { lat: b.pickup_lat, lng: b.pickup_lng },
                icon: { url: 'https://maps.google.com/mapfiles/ms/icons/green-dot.png' },
                title: 'Your Pickup'
            });
        }
    });
    // Start polling
    DRIVER_BOOKINGS.forEach(updateDriverLocation);
    setInterval(() => DRIVER_BOOKINGS.forEach(updateDriverLocation), 15000);
}

function updateDriverLocation(booking) {
    fetch(`/api/driver-location/${booking.driver}`)
        .then(r => r.json())
        .then(data => {
            const statsEl = document.getElementById(`driver-stats-${booking.id}`);
            const distEl  = document.getElementById(`driver-dist-val-${booking.id}`);
            const etaEl   = document.getElementById(`driver-eta-val-${booking.id}`);
            const trackEl = document.getElementById(`track-btn-${booking.id}`);
            const mapEl   = document.getElementById(`driver-map-${booking.id}`);

            if (!data.lat) {
                if (mapEl && mapEl.children.length === 0)
                    mapEl.innerHTML = '<span style="color:#9ca3af;font-size:.82rem;"><i class="bi bi-geo-alt me-1"></i>Driver location not available yet</span>';
                return;
            }

            const driverPos = { lat: data.lat, lng: data.lng };

            // Update map marker
            const map    = driverMaps[booking.id];
            const marker = driverMarkers[booking.id];
            if (map && marker) {
                marker.setPosition(driverPos);
                map.panTo(driverPos);
            }

            // Live track button
            if (trackEl) {
                const dest = booking.pickup_lat
                    ? `${booking.pickup_lat},${booking.pickup_lng}`
                    : `${data.lat},${data.lng}`;
                trackEl.href = `https://www.google.com/maps/dir/${data.lat},${data.lng}/${dest}`;
                trackEl.style.display = 'inline-flex';
            }

            // Distance Matrix for real road distance + ETA
            if (booking.pickup_lat && window.google) {
                const svc = new google.maps.DistanceMatrixService();
                svc.getDistanceMatrix({
                    origins:      [driverPos],
                    destinations: [{ lat: booking.pickup_lat, lng: booking.pickup_lng }],
                    travelMode:   google.maps.TravelMode.DRIVING,
                    unitSystem:   google.maps.UnitSystem.METRIC
                }, (res, status) => {
                    if (status !== 'OK') return;
                    const el = res.rows[0].elements[0];
                    if (el.status !== 'OK') return;
                    if (statsEl) statsEl.style.display = 'grid';
                    if (distEl)  distEl.textContent = el.distance.text;
                    if (etaEl)   etaEl.textContent  = el.duration.text;
                });
            }
        })
        .catch(() => {});
}"""

content = re.sub(
    r'// .{0,30}Driver location polling.*?if \(DRIVER_BOOKINGS\.length > 0\) \{.*?\}',
    new_js, content, flags=re.DOTALL
)

# ── 3. Replace Google Maps script tag (or add before </script>) ────────────
# Remove old haversineKm / etaText if present
content = re.sub(r'function haversineKm\(.*?\}\n\n', '', content, flags=re.DOTALL)
content = re.sub(r'function etaText\(.*?\}\n\n', '', content, flags=re.DOTALL)

# Add Google Maps JS API script tag before </body>
maps_tag = '\n<script src="https://maps.googleapis.com/maps/api/js?key={{ google_maps_key }}&libraries=places&callback=initDriverMaps" async defer></script>\n'
if 'maps.googleapis.com' not in content:
    content = content.replace('</body>', maps_tag + '</body>')

with open('templates/rider_bookings.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
