with open('templates/booking.html', encoding='utf-8') as f:
    c = f.read().replace('\r\n', '\n').replace('\r', '\n')

old = "function closeFullscreenMap() {\n    document.getElementById('fullscreenMapOverlay').classList.remove('show');\n\n    document.body.classList.remove('map-fullscreen');\n    closeFsSearch();\n\n    fsActiveType = null;\n}"

new = "function closeFullscreenMap() {\n    document.getElementById('fullscreenMapOverlay').classList.remove('show');\n    document.body.classList.remove('map-fullscreen');\n    const sbInput = document.getElementById('fs-sb-input');\n    if (sbInput) sbInput.value = '';\n    fsActiveType = null;\n}"

if old in c:
    c = c.replace(old, new, 1)
    print('OK')
else:
    print('NOT matched')

with open('templates/booking.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('done')
