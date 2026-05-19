with open('templates/booking.html', encoding='utf-8') as f:
    c = f.read().replace('\r\n', '\n').replace('\r', '\n')

# 1. Replace the fullscreen overlay HTML topbar + search results div
old_html = """    <!-- Top bar: search + exit -->

    <div class="fs-topbar">
        <input type="text" id="fsSearchInput" placeholder="Search location..." autocomplete="off">
        <button class="fs-search-btn" onmousedown="event.preventDefault(); triggerFsSearch();" aria-label="Search">
            <i class="bi bi-search"></i>
        </button>
        <button class="fs-exit-btn" onclick="closeFullscreenMap()" aria-label="Close map">
            <i class="bi bi-x-lg"></i> Exit
        </button>
    </div>
    <!-- Search results: fixed below topbar -->
    <div id="fsSearchResults"></div>"""

new_html = """    <!-- Top bar: exit only -->
    <div class="fs-topbar" style="justify-content:flex-end;">
        <button class="fs-exit-btn" onclick="closeFullscreenMap()" aria-label="Close map">
            <i class="bi bi-x-lg"></i> Exit
        </button>
    </div>"""

if old_html in c:
    c = c.replace(old_html, new_html, 1)
    print('HTML topbar replaced OK')
else:
    print('HTML topbar NOT matched')

# 2. Replace the fs-topbar CSS to be minimal
old_css = """        .fs-topbar {
            background: #0d6efd;
            padding: 10px 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            z-index: 10000;
        }
        .fs-topbar input {
            flex: 1;
            border-radius: 8px 0 0 8px;
            border: none;
            padding: 8px 12px;
            font-size: .9rem;
            outline: none;
        }
        .fs-search-btn {
            background: #fff;
            border: none;
            border-radius: 0 8px 8px 0;
            padding: 8px 14px;
            color: #0d6efd;
            font-size: 1rem;
            cursor: pointer;
            flex-shrink: 0;
        }
        .fs-search-btn:hover { background: #e9ecef; }
        .fs-exit-btn {
            background: rgba(255,255,255,.2);
            border: none;
            color: #fff;
            border-radius: 8px;
            padding: 8px 14px;
            font-weight: 700;
            font-size: .9rem;
            cursor: pointer;
            white-space: nowrap;
        }
        .fs-exit-btn:hover { background: rgba(255,255,255,.35); }"""

new_css = """        .fs-topbar {
            background: #0d6efd;
            padding: 10px 14px;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            z-index: 10000;
        }
        .fs-exit-btn {
            background: rgba(255,255,255,.2);
            border: none;
            color: #fff;
            border-radius: 8px;
            padding: 8px 14px;
            font-weight: 700;
            font-size: .9rem;
            cursor: pointer;
            white-space: nowrap;
        }
        .fs-exit-btn:hover { background: rgba(255,255,255,.35); }
        /* Google SearchBox inside map */
        #fs-google-searchbox {
            position: absolute;
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            width: 88%;
            max-width: 480px;
            z-index: 10001;
        }
        #fs-google-searchbox input {
            width: 100%;
            padding: 10px 16px;
            border-radius: 8px;
            border: none;
            font-size: .95rem;
            box-shadow: 0 2px 12px rgba(0,0,0,.3);
            outline: none;
        }"""

if old_css in c:
    c = c.replace(old_css, new_css, 1)
    print('CSS replaced OK')
else:
    print('CSS NOT matched')

# 3. Replace the Search input setup in openFullscreenMap with Google SearchBox
old_js = """    // Search input
    const fsInput = document.getElementById('fsSearchInput');
    fsInput.value = '';

    // Attach Google Places Autocomplete to fullscreen search input
    if (!fsInput._autocomplete && google.maps.places?.Autocomplete) {
        const fsAc = new google.maps.places.Autocomplete(fsInput, {
            componentRestrictions: { country: 'in' },
            fields: ['geometry', 'name', 'formatted_address']
        });
        fsAc.addListener('place_changed', () => {
            const place = fsAc.getPlace();
            if (place?.geometry?.location) {
                fsMap.setCenter(place.geometry.location);
                fsMap.setZoom(15);
                placeFsPin(place.geometry.location);
                closeFsSearch();
            }
        });
        fsInput._autocomplete = fsAc;
    }

    let fsTimer;
    fsInput.oninput = function() {
        clearTimeout(fsTimer);
        const q = this.value.trim();
        if (q.length < 3) { closeFsSearch(); return; }
        fsTimer = setTimeout(() => fetchFsSuggestions(q), 400);
    };
    fsInput.onkeydown = function(e) {
        if (e.key === 'Enter') { e.preventDefault(); triggerFsSearch(); }
    };"""

new_js = """    // Google SearchBox inside the map
    if (!window._fsSearchBox) {
        const sbInput = document.createElement('input');
        sbInput.type = 'text';
        sbInput.placeholder = 'Search location...';
        sbInput.id = 'fs-sb-input';
        const sbWrap = document.createElement('div');
        sbWrap.id = 'fs-google-searchbox';
        sbWrap.appendChild(sbInput);
        document.getElementById('fullscreenMap').appendChild(sbWrap);

        const searchBox = new google.maps.places.SearchBox(sbInput);
        fsMap.controls[google.maps.ControlPosition.TOP_CENTER].push(sbWrap);

        searchBox.addListener('places_changed', () => {
            const places = searchBox.getPlaces();
            if (!places || !places.length) return;
            const place = places[0];
            if (!place.geometry?.location) return;
            fsMap.setCenter(place.geometry.location);
            fsMap.setZoom(15);
            placeFsPin(place.geometry.location);
        });

        fsMap.addListener('bounds_changed', () => {
            searchBox.setBounds(fsMap.getBounds());
        });

        window._fsSearchBox = searchBox;
    }"""

if old_js in c:
    c = c.replace(old_js, new_js, 1)
    print('JS search input replaced OK')
else:
    print('JS search input NOT matched')
    idx = c.find('// Search input')
    print(repr(c[idx:idx+600]))

with open('templates/booking.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('done')
