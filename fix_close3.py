with open('templates/booking.html', encoding='utf-8') as f:
    lines = f.readlines()

out = []
for line in lines:
    if line.strip() == 'closeFsSearch();':
        out.append(line.replace('closeFsSearch();', "const sbInput = document.getElementById('fs-sb-input'); if (sbInput) sbInput.value = '';"))
    else:
        out.append(line)

with open('templates/booking.html', 'w', encoding='utf-8') as f:
    f.writelines(out)
print('done')
