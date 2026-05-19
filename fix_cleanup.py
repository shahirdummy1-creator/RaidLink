with open('templates/booking.html', encoding='utf-8') as f:
    c = f.read().replace('\r\n', '\n').replace('\r', '\n')

# Remove fetchFsSuggestions, triggerFsSearch, closeFsSearch functions - no longer needed
import re

# Remove fetchFsSuggestions
c = re.sub(r'\nasync function fetchFsSuggestions\(query\) \{[\s\S]*?^\}\n', '\n', c, count=1, flags=re.MULTILINE)

# Remove triggerFsSearch
c = re.sub(r'\nasync function triggerFsSearch\(\) \{[\s\S]*?^\}\n', '\n', c, count=1, flags=re.MULTILINE)

# Remove closeFsSearch
c = re.sub(r'\nfunction closeFsSearch\(\) \{[\s\S]*?^\}\n', '\n', c, count=1, flags=re.MULTILINE)

# Remove selectFsResult references to fsSearchInput
c = c.replace("    document.getElementById('fsSearchInput').value = place.description.split(',')[0];\n    closeFsSearch();\n", '')

# Remove #fsSearchResults CSS
c = re.sub(r'\n        /\* Search results dropdown \*/\n        #fsSearchResults \{[\s\S]*?#fsSearchResults\.show \{ display: block; \}\n', '\n', c, count=1)

# Remove .fs-topbar input and .fs-search-btn from mobile CSS
c = c.replace("            .fs-topbar input { min-height: 44px; font-size: 1rem; }\n", '')
c = c.replace("            .fs-search-btn { min-height: 44px; padding: 8px 16px; }\n", '')

with open('templates/booking.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('done')
