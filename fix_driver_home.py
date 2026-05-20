with open('templates/driver_home.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out = []
i = 0
while i < len(lines):
    line = lines[i]

    # 1. Inject distance inline into Drop label div (line 489)
    if '>Drop</div>' in line:
        line = line.replace(
            '>Drop</div>',
            '>Drop &nbsp;<span style="font-size:.65rem;color:#6b7280;font-weight:600;">${b.distance_km} km total</span></div>'
        )

    # 2. Remove the Distance tile block (lines 498-500: outer div + distance div + closing div)
    if 'background:#f8faff;border:1px solid #e0e7ff' in line and i+1 < len(lines) and 'distance_km' in lines[i+1]:
        i += 3  # skip outer div, distance div, closing div
        continue

    out.append(line)
    i += 1

# Fix grid to 1 column since Distance tile is removed
result = ''.join(out)
result = result.replace(
    'grid-template-columns:1fr 1fr;gap:8px;margin-bottom:16px;',
    'grid-template-columns:1fr;gap:8px;margin-bottom:16px;'
)

with open('templates/driver_home.html', 'w', encoding='utf-8') as f:
    f.write(result)

# Verify
with open('templates/driver_home.html', 'r', encoding='utf-8') as f:
    for i, l in enumerate(f, 1):
        if ('Drop' in l and 'distance_km' in l) or ('distance_km' in l and 'f8faff' not in l):
            print(f"Line {i}:", l.rstrip())
