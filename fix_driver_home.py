with open('templates/driver_home.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out = []
i = 0
while i < len(lines):
    line = lines[i]

    # 1. Replace pickupDistHtml variable declaration and block
    if "let pickupDistHtml = '';" in line:
        # Emit new variable
        out.append("        let pickupDistInline = '';\n")
        # Skip until we hit the closing } of the else if block
        # Consume: if block + else if block
        i += 1
        depth = 0
        started = False
        while i < len(lines):
            l = lines[i]
            if '{' in l: depth += l.count('{'); started = True
            if '}' in l: depth -= l.count('}')
            i += 1
            if started and depth <= 0:
                break
        # Now emit the new if/else if block
        out.append("        if (b.pickup_lat && b.pickup_lng && driverLat !== null && driverLng !== null) {\n")
        out.append("            const d = haversineKm(driverLat, driverLng, parseFloat(b.pickup_lat), parseFloat(b.pickup_lng));\n")
        out.append('            pickupDistInline = `<span style="font-size:.75rem;color:#d97706;font-weight:600;margin-left:6px;"><i class="bi bi-car-front-fill"></i> ${d.toFixed(1)} km away</span>`;\n')
        out.append("        } else if (b.pickup_lat && b.pickup_lng && navigator.geolocation) {\n")
        out.append("            navigator.geolocation.getCurrentPosition(pos => {\n")
        out.append("                driverLat = pos.coords.latitude;\n")
        out.append("                driverLng = pos.coords.longitude;\n")
        out.append("                renderBookingCard(b);\n")
        out.append("            }, () => {});\n")
        out.append("        }\n")
        continue

    # 2. Inject pickupDistInline into pickup location value div
    if 'font-weight:600;color:#111827;font-size:.9rem;">${capitalize(b.pickup_location)}</div>' in line:
        line = line.replace(
            '>${capitalize(b.pickup_location)}</div>',
            '>${capitalize(b.pickup_location)}${pickupDistInline}</div>'
        )

    # 3. Remove ${pickupDistHtml} tile line
    if '${pickupDistHtml}' in line:
        i += 1
        continue

    # 4. Fix grid columns — remove dynamic expression
    if "grid-template-columns:${pickupDistHtml ? '1fr 1fr 1fr' : '1fr 1fr'}" in line:
        line = line.replace(
            "grid-template-columns:${pickupDistHtml ? '1fr 1fr 1fr' : '1fr 1fr'}",
            "grid-template-columns:1fr 1fr"
        )

    out.append(line)
    i += 1

with open('templates/driver_home.html', 'w', encoding='utf-8') as f:
    f.writelines(out)

print("Done")
