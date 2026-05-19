with open('templates/driver_home.html', 'rb') as f:
    content = f.read()

old = b'<div style="font-weight:600;color:#111827;font-size:.9rem;">${capitalize(b.drop_location)}<span style="font-size:.75rem;color:#6b7280;font-weight:600;margin-left:6px;"><i class=\\"bi bi-signpost-2\\"></i> ${b.distance_km} km</span></div>'
new = b'<div style="font-weight:600;color:#111827;font-size:.9rem;">${capitalize(b.drop_location)}<span style="font-size:.75rem;color:#6b7280;font-weight:600;margin-left:6px;"><i class="bi bi-signpost-2"></i> ${b.distance_km} km</span></div>'

content = content.replace(old, new)

with open('templates/driver_home.html', 'wb') as f:
    f.write(content)

# Verify
with open('templates/driver_home.html', 'r', encoding='utf-8') as f:
    for i, l in enumerate(f, 1):
        if 'drop_location' in l and 'distance_km' in l:
            print(f"Line {i}:", l.rstrip())
