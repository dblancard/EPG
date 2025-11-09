// Channels are now vertically scrollable; no pagination needed
const CHANNELS_PER_PAGE = null;
const MINUTES_PER_SLOT = 15;
const SLOT_WIDTH_PX = 100;

let state = {
    channels: [],
    allChannelsWithPrograms: [],
    currentPage: 1, // deprecated
    totalPages: 1,  // deprecated
    country: localStorage.getItem('selectedCountry') || 'CA',
    hideEmpty: true,
    showFavoritesOnly: false,
    favorites: JSON.parse(localStorage.getItem('favoriteChannels') || '[]'),
    loading: false,
    startTime: null,
    endTime: null
};

function toggleFavorite(channelId) {
    const index = state.favorites.indexOf(channelId);
    if (index > -1) {
        state.favorites.splice(index, 1);
    } else {
        state.favorites.push(channelId);
    }
    localStorage.setItem('favoriteChannels', JSON.stringify(state.favorites));
    // Don't re-render unless we're in favorites-only mode and need to hide/show channels
    if (state.showFavoritesOnly) {
        renderGrid();
    }
}

function isFavorite(channelId) {
    return state.favorites.includes(channelId);
}

// Parse a datetime string from the server and return a Date in the browser's timezone.
// Heuristic:
// - If the string already includes a timezone (Z or +/-HH:MM), rely on Date to convert.
// - If it's a naive timestamp (no TZ), treat it as UTC to avoid rendering in UTC-looking times.
function parseServerDate(dtStr) {
    if (!dtStr) return null;
    let s = String(dtStr).trim();
    // If already ISO with timezone info
    if (s.endsWith('Z') || /[+-]\d{2}:?\d{2}$/.test(s)) {
        return new Date(s);
    }
    // Normalize: replace space with 'T' if present and append 'Z' to treat as UTC
    if (s.indexOf(' ') > -1 && s.indexOf('T') === -1) {
        s = s.replace(' ', 'T');
    }
    // If has T but no timezone, assume UTC
    if (/T\d{2}:\d{2}(:\d{2}(\.\d+)?)?$/.test(s)) {
        s = s + 'Z';
    }
    return new Date(s);
}

function formatTimeLocal(dateObj) {
    if (!dateObj) return '';
    return dateObj.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit', hour12: true });
}

// Map ISO 3166-1 alpha-2 codes to country names.
// Fallback: if a code isn't present here (or isn't ISO), we display the code as-is.
const ISO_COUNTRY_NAMES = {
    'US': 'United States',
    'CA': 'Canada',
    'GB': 'United Kingdom',
    'FR': 'France',
    'DE': 'Germany',
    'ES': 'Spain',
    'IT': 'Italy',
    'PT': 'Portugal',
    'NL': 'Netherlands',
    'BE': 'Belgium',
    'CH': 'Switzerland',
    'AT': 'Austria',
    'IE': 'Ireland',
    'NO': 'Norway',
    'SE': 'Sweden',
    'DK': 'Denmark',
    'FI': 'Finland',
    'PL': 'Poland',
    'CZ': 'Czechia',
    'SK': 'Slovakia',
    'HU': 'Hungary',
    'RO': 'Romania',
    'BG': 'Bulgaria',
    'GR': 'Greece',
    'TR': 'Turkey',
    'RU': 'Russia',
    'UA': 'Ukraine',
    'RS': 'Serbia',
    'HR': 'Croatia',
    'SI': 'Slovenia',
    'BA': 'Bosnia and Herzegovina',
    'MK': 'North Macedonia',
    'ME': 'Montenegro',
    'AL': 'Albania',
    'LT': 'Lithuania',
    'LV': 'Latvia',
    'EE': 'Estonia',
    'LU': 'Luxembourg',
    'IS': 'Iceland',
    'LI': 'Liechtenstein',
    'MC': 'Monaco',
    'SM': 'San Marino',
    'AD': 'Andorra',
    'VA': 'Vatican City',
    'BR': 'Brazil',
    'AR': 'Argentina',
    'MX': 'Mexico',
    'CL': 'Chile',
    'CO': 'Colombia',
    'PE': 'Peru',
    'VE': 'Venezuela',
    'UY': 'Uruguay',
    'PY': 'Paraguay',
    'BO': 'Bolivia',
    'EC': 'Ecuador',
    'CR': 'Costa Rica',
    'PA': 'Panama',
    'PR': 'Puerto Rico',
    'DO': 'Dominican Republic',
    'JM': 'Jamaica',
    'AU': 'Australia',
    'NZ': 'New Zealand',
    'JP': 'Japan',
    'KR': 'South Korea',
    'CN': 'China',
    'HK': 'Hong Kong',
    'TW': 'Taiwan',
    'IN': 'India',
    'TH': 'Thailand',
    'VN': 'Vietnam',
    'MY': 'Malaysia',
    'SG': 'Singapore',
    'PH': 'Philippines',
    'ID': 'Indonesia',
    'AE': 'United Arab Emirates',
    'SA': 'Saudi Arabia',
    'EG': 'Egypt',
    'MA': 'Morocco',
    'TN': 'Tunisia',
    'DZ': 'Algeria',
    'ZA': 'South Africa',
    'NG': 'Nigeria',
    'KE': 'Kenya',
    'GH': 'Ghana',
    'IL': 'Israel',
    'QA': 'Qatar',
    'KW': 'Kuwait',
    'BH': 'Bahrain',
    'OM': 'Oman',
    'JO': 'Jordan',
    'LB': 'Lebanon'
};

function getCountryName(code) {
    const c = (code || '').toUpperCase();
    return ISO_COUNTRY_NAMES[c] || c;
}

async function loadCountries() {
    const resp = await fetch('/api/countries');
    const data = await resp.json();
    const select = document.getElementById('country-filter');
    select.innerHTML = '';
    data.countries.forEach(function(c) {
        const opt = document.createElement('option');
        opt.value = c.code;
        // Show full country name when available; otherwise show the code.
        const label = getCountryName(c.code);
        opt.textContent = label;
        opt.title = label !== c.code ? (c.code + ' - ' + label) : c.code;
        select.appendChild(opt);
    });
    // Restore saved country or default to first available
    const savedCountry = localStorage.getItem('selectedCountry');
    if (savedCountry && data.countries.some(c => c.code === savedCountry)) {
        select.value = savedCountry;
        state.country = savedCountry;
    } else if (data.countries.length > 0) {
        select.value = data.countries[0].code;
        state.country = data.countries[0].code;
    }
}

document.addEventListener('DOMContentLoaded', async function() {
    const now = new Date();
    // Round start time down to nearest 30 minutes
    const startMs = now.getTime() - (60 * 60 * 1000);
    const startDate = new Date(startMs);
    const mins = startDate.getMinutes();
    const roundedMins = mins < 30 ? 0 : 30;
    startDate.setMinutes(roundedMins, 0, 0);
    state.startTime = startDate;
    state.endTime = new Date(state.startTime.getTime() + (12 * 60 * 60 * 1000));
    
    // Load available countries and populate dropdown
    await loadCountries();
    
    document.getElementById('country-filter').addEventListener('change', function(e) {
        state.country = e.target.value;
        localStorage.setItem('selectedCountry', state.country);
        loadData();
    });
    
    document.getElementById('hide-empty-channels').addEventListener('change', function(e) {
        state.hideEmpty = e.target.checked;
        renderGrid();
    });
    
    document.getElementById('show-favorites-only').addEventListener('change', function(e) {
        state.showFavoritesOnly = e.target.checked;
        renderGrid();
    });
    
    // Horizontal time navigation via buttons and keyboard
    const hoursPerClick = 1;
    const scrollAmountPx = (60 / MINUTES_PER_SLOT) * SLOT_WIDTH_PX * hoursPerClick;
    
    const getContainer = () => document.getElementById('tv-guide-container');
    
    const updateScrollButtons = () => {
        const containerEl = getContainer();
        const leftBtn = document.getElementById('scroll-left');
        const rightBtn = document.getElementById('scroll-right');
        if (!leftBtn || !rightBtn || !containerEl) return;
        leftBtn.disabled = containerEl.scrollLeft <= 0;
        const maxScroll = containerEl.scrollWidth - containerEl.clientWidth - 1;
        rightBtn.disabled = containerEl.scrollLeft >= maxScroll;
    };
    
    const scrollByAmount = (dir) => {
        const containerEl = getContainer();
        if (!containerEl) return;
        containerEl.scrollBy({ left: dir * scrollAmountPx, behavior: 'smooth' });
        // Update buttons after the smooth scroll ends (approximate)
        setTimeout(updateScrollButtons, 350);
    };
    
    const leftBtn = document.getElementById('scroll-left');
    const rightBtn = document.getElementById('scroll-right');
    if (leftBtn) leftBtn.addEventListener('click', () => scrollByAmount(-1));
    if (rightBtn) rightBtn.addEventListener('click', () => scrollByAmount(1));
    
    const containerEl = getContainer();
    if (containerEl) {
        containerEl.addEventListener('scroll', updateScrollButtons);
    }
    
    // Keyboard controls: Left/Right = scroll time, PageUp/PageDown = scroll channels
    window.addEventListener('keydown', function(e) {
        const container = getContainer();
        if (!container) return;
        
        // Ignore if user is typing in an input/select
        const target = e.target;
        if (target.tagName === 'INPUT' || target.tagName === 'SELECT' || target.tagName === 'TEXTAREA') {
            return;
        }
        
        const handled = ['ArrowLeft', 'ArrowRight', 'PageUp', 'PageDown'].includes(e.key);
        if (!handled) return;
        
        e.preventDefault();
        e.stopPropagation();
        
        switch(e.key) {
            case 'ArrowLeft':
                scrollByAmount(-1);
                break;
            case 'ArrowRight':
                scrollByAmount(1);
                break;
            case 'PageUp':
                container.scrollBy({ top: -container.clientHeight * 0.8, behavior: 'smooth' });
                break;
            case 'PageDown':
                container.scrollBy({ top: container.clientHeight * 0.8, behavior: 'smooth' });
                break;
        }
    }, true);
    
    loadData().then(() => {
        // Initialize scroll button state after content renders
        setTimeout(() => {
            const container = document.getElementById('tv-guide-container');
            if (container) {
                container.scrollLeft = 0;
                container.scrollTop = 0;
                // Update nav buttons state now that sizes are known
                updateScrollButtons();
            }
        }, 0);
    });
    
    // Update current time indicator every minute
    setInterval(function() {
        updateCurrentTimeIndicator();
    }, 60000);
});

function updateCurrentTimeIndicator() {
    const indicator = document.querySelector('.current-time-indicator');
    if (!indicator) return;
    
    const now = new Date();
    const leftOffset = 200; // channel column width
    const timePosition = (now - state.startTime) / 60000 / MINUTES_PER_SLOT * SLOT_WIDTH_PX;
    
    if (now >= state.startTime && now <= state.endTime && timePosition >= 0) {
        const leftPos = timePosition + leftOffset;
        indicator.style.left = leftPos + 'px';
        indicator.style.display = 'block';
    } else {
        indicator.style.display = 'none';
    }
}

async function loadData() {
    const gridEl = document.getElementById('tv-guide-grid');
    const loadingIndicator = document.getElementById('loading-indicator');
    
    if (gridEl) gridEl.classList.add('loading');
    if (loadingIndicator) loadingIndicator.style.display = 'block';
    state.currentPage = 1;
    
    // Fetch all channels by paginating through API (max 100 per request)
    let allChannels = [];
    let page = 1;
    let totalPages = 1;
    
    do {
        const resp = await fetch('/api/channels?country=' + state.country + '&page=' + page + '&per_page=100');
        const data = await resp.json();
        allChannels = allChannels.concat(data.channels);
        totalPages = data.total_pages;
        page++;
    } while (page <= totalPages);
    
    // Store ALL channels
    state.allChannelsWithPrograms = allChannels;
    
    // Load programs only for channels that have program_count > 0
    const channelsToLoad = allChannels.filter(c => c.program_count > 0);
    await Promise.all(channelsToLoad.map(async function(ch) {
        const r = await fetch('/api/schedule/' + ch.id);
        const d = await r.json();
        ch.programs = d.programs || [];
    }));
    
    // Set empty programs array for channels without programs
    allChannels.forEach(ch => {
        if (!ch.programs) ch.programs = [];
    });
    
    if (loadingIndicator) loadingIndicator.style.display = 'none';
    renderGrid();
    
    // Remove blur after a short delay to let the render complete
    setTimeout(function() {
        const grid = document.getElementById('tv-guide-grid');
        if (grid) grid.classList.remove('loading');
    }, 100);
}

function renderGrid() {
    // Filter based on program_count from database (more reliable than checking loaded programs in time window)
    let filtered = state.allChannelsWithPrograms;
    
    if (state.hideEmpty) {
        filtered = filtered.filter(c => c.program_count > 0);
    }
    
    if (state.showFavoritesOnly) {
        filtered = filtered.filter(c => isFavorite(c.id));
    }
    
    state.channels = filtered;
    const pageChannels = filtered; // show all; vertical scroll handles overflow
    
    const totalMinutes = (state.endTime - state.startTime) / 60000;
    const numSlots = Math.ceil(totalMinutes / MINUTES_PER_SLOT);
    
    // Calculate current time indicator position (only show if within grid time range)
    const now = new Date();
    const leftOffset = 200; // channel column width
    const timePosition = (now - state.startTime) / 60000 / MINUTES_PER_SLOT * SLOT_WIDTH_PX;
    const currentTimeIndicatorHtml = (now >= state.startTime && now <= state.endTime && timePosition >= 0) 
        ? '<div class="current-time-indicator" style="left: ' + (timePosition + leftOffset) + 'px;"></div>'
        : '';
    
    // Build time header row
    let html = '<div class="guide-grid">';
    html += '<div class="time-header-row">';
    html += '<div class="corner-cell">Channels</div>';
    html += '<div class="time-slots-cell">';
    html += '<div class="time-slots">';
    
    for (let i = 0; i < numSlots; i++) {
        const t = new Date(state.startTime.getTime() + i * MINUTES_PER_SLOT * 60000);
        const hours24 = t.getHours();
        const h = hours24 % 12 || 12;
        const m = ('0' + t.getMinutes()).slice(-2);
        const ampm = hours24 >= 12 ? 'PM' : 'AM';
        // Show label on every hour and half hour
        const mins = t.getMinutes();
        const label = (mins === 0 || mins === 30) ? h + ':' + m + ' ' + ampm : '&nbsp;';
        html += '<div class="time-slot" style="width:' + SLOT_WIDTH_PX + 'px">' + label + '</div>';
    }
    
    html += '</div>'; // close time-slots
    html += '</div>'; // close time-slots-cell
    html += '</div>'; // close time-header-row
    
    // Build channel rows
    pageChannels.forEach(function(ch) {
        const name = ch.name.indexOf('|') > 0 ? ch.name.split('|')[1].trim() : ch.name;
        const progs = (ch.programs || []).filter(p => parseServerDate(p.end_time) > state.startTime && parseServerDate(p.start_time) < state.endTime);
        const isFav = isFavorite(ch.id);
        
    html += '<div class="channel-row">';
    html += '<div class="channel-label" data-channel-id="' + ch.id + '">';
        html += '<div class="channel-label-content">';
        html += '<input type="checkbox" class="favorite-checkbox" data-channel-id="' + ch.id + '" ' + (isFav ? 'checked' : '') + ' title="Add to favorites">';
        if (ch.icon_url) html += '<img src="' + ch.icon_url + '" onerror="this.style.display=\'none\'">';
        html += '<span>' + name + '</span>';
        html += '</div>'; // close channel-label-content
        html += '</div>'; // close channel-label
        html += '<div class="channel-programs-cell">';
        html += '<div class="channel-programs">';
        
        // Lay out programs along the timeline with exact gaps and basic overlap handling
        let cursor = new Date(state.startTime.getTime());
        progs.forEach(function(p) {
            const st = parseServerDate(p.start_time);
            const et = parseServerDate(p.end_time);

            if (!st || !et) return;
            // Skip if outside range (extra guard; we filtered above)
            if (et <= state.startTime || st >= state.endTime) return;

            // Insert a gap if there's time between the cursor and this program's start
            let gapStart = cursor > state.startTime ? cursor : state.startTime;
            if (st > gapStart) {
                const gapMinutes = (st - gapStart) / 60000;
                if (gapMinutes > 0.5) {
                    const gapWidth = (gapMinutes / MINUTES_PER_SLOT) * SLOT_WIDTH_PX;
                    html += '<div class="program-gap" style="width:' + gapWidth + 'px"></div>';
                }
            }

            // Clamp visible start to the max of state window and cursor to avoid rendering overlapped portion twice
            const visibleStart = new Date(Math.max(st.getTime(), state.startTime.getTime(), cursor.getTime()));
            const visibleEnd = new Date(Math.min(et.getTime(), state.endTime.getTime()));

            const visibleDurMinutes = (visibleEnd - visibleStart) / 60000;
            if (visibleDurMinutes <= 0.5) {
                // Nothing meaningful to render
                cursor = new Date(Math.max(cursor.getTime(), et.getTime()));
                return;
            }

            // Use exact width (no rounding) to avoid cumulative overlap; enforce a tiny minimum for visibility
            const widthPx = Math.max(4, (visibleDurMinutes / MINUTES_PER_SLOT) * SLOT_WIDTH_PX);

            // Create tooltip text with local times
            const tooltipText = p.title + '\n' + formatTimeLocal(st) + ' - ' + formatTimeLocal(et) + (p.description ? '\n\n' + p.description : '') + (p.category ? '\n\nCategory: ' + p.category : '');

            html += '<div class="program-block" style="width:' + widthPx + 'px" title="' + tooltipText.replace(/\"/g, '&quot;') + '">';
            html += '<div class="program-title">' + p.title + '</div>';
            html += '<div class="program-time">' + formatTimeLocal(st) + ' - ' + formatTimeLocal(et) + '</div>';
            if (p.description) {
                html += '<div class="program-description">' + p.description + '</div>';
            }
            html += '</div>'; // close program-block

            // Advance cursor to the end of what we just placed (or program's real end if it was later)
            cursor = new Date(Math.max(cursor.getTime(), et.getTime(), visibleEnd.getTime()));
        });
        
        html += '</div>'; // close channel-programs
        html += '</div>'; // close channel-programs-cell
        html += '</div>'; // close channel-row
    });
    
    html += currentTimeIndicatorHtml; // add current time indicator
    html += '</div>'; // close guide-grid
    document.getElementById('tv-guide-grid').innerHTML = html;
    
    // Attach event listeners to favorite checkboxes
    document.querySelectorAll('.favorite-checkbox').forEach(function(checkbox) {
        checkbox.addEventListener('change', function(e) {
            e.stopPropagation();
            const channelId = parseInt(this.getAttribute('data-channel-id'));
            toggleFavorite(channelId);
        });
    });
    
    // Hover debug: show raw channel data when hovering channel label cell
    setupChannelHoverDebug();
    
    // Update scroll button state after render
    const containerEl = document.getElementById('tv-guide-container');
    if (containerEl) {
        const leftBtn = document.getElementById('scroll-left');
        const rightBtn = document.getElementById('scroll-right');
        if (leftBtn && rightBtn) {
            leftBtn.disabled = containerEl.scrollLeft <= 0;
            rightBtn.disabled = (containerEl.scrollWidth - containerEl.clientWidth - 1) <= 0;
        }
    }
}

function setupChannelHoverDebug() {
    const panel = document.getElementById('hover-debug-panel');
    const container = document.getElementById('tv-guide-container');
    if (!panel || !container) return;
    let panelPinned = false;
    let labelHovering = false;
    let panelHovering = false;

    function renderPanelContent(ch) {
        try {
            const json = JSON.stringify(ch, null, 2);
            const title = `${ch.name} (id=${ch.id})`;
            panel.innerHTML = `
                <div class="hover-debug-header">
                    <div class="hover-debug-title" title="${title}">${title}</div>
                    <div class="hover-debug-actions">
                        <button type="button" id="hover-debug-pin" class="${panelPinned ? '' : 'secondary'}">${panelPinned ? 'Unpin' : 'Pin'}</button>
                        <button type="button" id="hover-debug-close" class="secondary">Close</button>
                    </div>
                </div>
                <pre style="margin:0;">${json.replace(/[<>&]/g, c => ({'<':'&lt;','>':'&gt;','&':'&amp;'}[c]))}</pre>
            `;
            // Wire buttons
            const pinBtn = document.getElementById('hover-debug-pin');
            const closeBtn = document.getElementById('hover-debug-close');
            if (pinBtn) pinBtn.onclick = function(ev){ ev.stopPropagation(); panelPinned = !panelPinned; renderPanelContent(ch); panel.classList.toggle('pinned', panelPinned); };
            if (closeBtn) closeBtn.onclick = function(ev){ ev.stopPropagation(); hidePanel(); };
        } catch (err) {
            panel.textContent = 'Error rendering raw data: ' + err;
        }
    }

    function showPanelForChannel(e, labelEl) {
        const idStr = labelEl.getAttribute('data-channel-id');
        if (!idStr) return;
        const cid = parseInt(idStr);
        const ch = (state.allChannelsWithPrograms || []).find(c => c.id === cid) || (state.channels || []).find(c => c.id === cid);
        if (!ch) return;
        renderPanelContent(ch);
        panel.style.display = 'block';
        if (!panelPinned) positionHoverPanel(e, panel, container);
    }

    function hidePanel() {
        panel.style.display = 'none';
        panelPinned = false;
        panel.classList.remove('pinned');
    }

    const onOver = function(e) {
        labelHovering = true;
        showPanelForChannel(e, e.currentTarget);
    };
    const onMove = function(e) {
        if (panel.style.display !== 'none' && !panelPinned) positionHoverPanel(e, panel, container);
    };
    const onLeave = function() {
        labelHovering = false;
        // Defer hide: only close if not pinned and not hovering panel
        setTimeout(() => {
            if (!panelPinned && !panelHovering) hidePanel();
        }, 50);
    };

    // Panel hover management
    panel.addEventListener('mouseenter', function(){ panelHovering = true; });
    panel.addEventListener('mouseleave', function(){
        panelHovering = false;
        if (!panelPinned && !labelHovering) hidePanel();
    });

    document.querySelectorAll('.channel-label').forEach(function(el) {
        el.removeEventListener('mouseover', onOver);
        el.removeEventListener('mousemove', onMove);
        el.removeEventListener('mouseleave', onLeave);
        el.addEventListener('mouseover', onOver);
        el.addEventListener('mousemove', onMove);
        el.addEventListener('mouseleave', onLeave);
    });
}

function positionHoverPanel(e, panel, container) {
    const padding = 12; // offset from cursor
    const containerRect = container.getBoundingClientRect();
    const panelRect = panel.getBoundingClientRect();

    // Compute position relative to container
    let left = e.clientX - containerRect.left + padding + container.scrollLeft;
    let top = e.clientY - containerRect.top + padding + container.scrollTop;

    // Clamp to keep panel within container viewport
    const maxLeft = container.scrollLeft + container.clientWidth - panelRect.width - 8;
    const maxTop = container.scrollTop + container.clientHeight - panelRect.height - 8;
    left = Math.max(container.scrollLeft + 4, Math.min(left, maxLeft));
    top = Math.max(container.scrollTop + 4, Math.min(top, maxTop));

    panel.style.left = left + 'px';
    panel.style.top = top + 'px';
}
