import re

with open('templates/rider_bookings.html', 'r', encoding='utf-8') as f:
    content = f.read()

# ── 1. Replace driver location HTML block ─────────────────────────────────
new_block = """{% if b.accepted_by %}
                <!-- Driver Location -->
                <div id="driver-loc-{{ b.id }}" style="padding:12px 20px;border-top:1px solid #f3f4f6;">
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
                    <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
                        <span id="driver-loc-status-{{ b.id }}" style="font-size:.8rem;color:#9ca3af;">
                            <i class="bi bi-arrow-clockwise me-1"></i>Fetching driver location&#8230;
                        </span>
                        <a id="track-btn-{{ b.id }}" href="#" target="_blank"
                           style="display:none;align-items:center;gap:6px;background:#0d6efd;color:#fff;padding:7px 16px;border-radius:8px;font-size:.82rem;font-weight:600;text-decoration:none;">
                            <i class="bi bi-geo-alt-fill"></i> View Driver Location
                        </a>
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

function updateDriverLocation(booking) {
    fetch(`/api/driver-location/${booking.driver}`)
        .then(r => r.json())
        .then(data => {
            const statsEl  = document.getElementById(`driver-stats-${booking.id}`);
            const distEl   = document.getElementById(`driver-dist-val-${booking.id}`);
            const etaEl    = document.getElementById(`driver-eta-val-${booking.id}`);
            const trackEl  = document.getElementById(`track-btn-${booking.id}`);
            const statusEl = document.getElementById(`driver-loc-status-${booking.id}`);

            if (!data.lat) {
                if (statusEl) statusEl.innerHTML = '<i class="bi bi-geo-alt me-1"></i>Driver location not available yet';
                return;
            }

            // Hide status text
            if (statusEl) statusEl.style.display = 'none';

            // Show View Driver Location button
            if (trackEl) {
                const dest = booking.pickup_lat
                    ? `${booking.pickup_lat},${booking.pickup_lng}`
                    : `${data.lat},${data.lng}`;
                trackEl.href = `https://www.google.com/maps/dir/${data.lat},${data.lng}/${dest}`;
                trackEl.style.display = 'inline-flex';
            }

            // Distance Matrix for real road distance + ETA
            if (booking.pickup_lat && window.google && google.maps) {
                new google.maps.DistanceMatrixService().getDistanceMatrix({
                    origins:      [{ lat: data.lat, lng: data.lng }],
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
}

function initDriverTracking() {
    if (DRIVER_BOOKINGS.length > 0) {
        DRIVER_BOOKINGS.forEach(updateDriverLocation);
        setInterval(() => DRIVER_BOOKINGS.forEach(updateDriverLocation), 15000);
    }
}"""

content = re.sub(
    r'// .{0,30}Driver location (polling|tracking).*?(?=\n</script>)',
    new_js, content, flags=re.DOTALL
)

# ── 3. Fix Google Maps script tag callback ─────────────────────────────────
content = re.sub(
    r'callback=initDriverMaps',
    'callback=initDriverTracking',
    content
)

# Remove map-related JS that's no longer needed
content = re.sub(r'const driverMaps\s*=.*?;\s*// bookingId.*\n', '', content)
content = re.sub(r'const driverMarkers\s*=.*?;\s*// bookingId.*\n', '', content)

with open('templates/rider_bookings.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
