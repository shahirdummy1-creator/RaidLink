with open('templates/booking.html', encoding='utf-8') as f:
    lines = f.readlines()

out = []
i = 0
skip_until = None
while i < len(lines):
    line = lines[i]
    stripped = line.strip()

    # Replace the topbar div (lines 396-405 approx) - detect by content
    if '<!-- Top bar: search + exit -->' in line:
        out.append('    <!-- Top bar: exit only -->\n')
        out.append('    <div class="fs-topbar" style="justify-content:flex-end;">\n')
        out.append('        <button class="fs-exit-btn" onclick="closeFullscreenMap()" aria-label="Close map">\n')
        out.append('            <i class="bi bi-x-lg"></i> Exit\n')
        out.append('        </button>\n')
        out.append('    </div>\n')
        # skip until after </div> of fs-topbar
        i += 1
        depth = 0
        while i < len(lines):
            l = lines[i]
            if '<div' in l: depth += 1
            if '</div>' in l:
                if depth == 0:
                    i += 1
                    break
                depth -= 1
            i += 1
        continue

    # Remove the fsSearchResults div line
    if '<div id="fsSearchResults"></div>' in line:
        i += 1
        continue

    out.append(line)
    i += 1

with open('templates/booking.html', 'w', encoding='utf-8') as f:
    f.writelines(out)
print('done, lines:', len(out))
