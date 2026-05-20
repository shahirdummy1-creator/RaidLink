with open('templates/driver_home.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out = []
i = 0
while i < len(lines):
    if '>Distance</div>' in lines[i] and i+1 < len(lines) and 'distance_km' in lines[i+1]:
        # Replace label line with value, skip the value line
        out.append(lines[i].replace('>Distance</div>', '>${b.distance_km} km</div>'))
        i += 2  # skip the value div line
    else:
        out.append(lines[i])
        i += 1

with open('templates/driver_home.html', 'w', encoding='utf-8') as f:
    f.writelines(out)

# Verify
with open('templates/driver_home.html', 'r', encoding='utf-8') as f:
    for i, l in enumerate(f, 1):
        if 'distance_km' in l:
            print(f"Line {i}:", l.rstrip())
