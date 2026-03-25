/**
 * LIVE DATA LOADER v2.0
 * =====================
 * Fetches data from /data/live-feed.json
 * 
 * TRANSPARENCY NOTE:
 * This is a 12-hour delayed relay from the tanks, automatically captured
 * and converted by THE BROADCASTER daemon (coordinated with THE SCHEDULER,
 * THE CARETAKER, and THE WEBMASTER).
 * 
 * Data is pruned: null thoughts, timeouts, and junk data removed for clean display.
 * Full and live logs available on request: research@digiquarium.org
 */

let liveFeed = null;
let lastUpdate = null;

// SVG avatars for each specimen
const SPECIMEN_SVGS = {
    'tank-01-adam': `<svg viewBox="0 0 40 40" width="32" height="32"><circle cx="20" cy="15" r="8" fill="#07CF8D"/><path d="M8 35 Q8 25 20 25 Q32 25 32 35" fill="#07CF8D"/><circle cx="17" cy="14" r="1.5" fill="#000"/><circle cx="23" cy="14" r="1.5" fill="#000"/></svg>`,
    'tank-02-eve': `<svg viewBox="0 0 40 40" width="32" height="32"><circle cx="20" cy="15" r="8" fill="#07DDE7"/><path d="M8 35 Q8 25 20 25 Q32 25 32 35" fill="#07DDE7"/><path d="M12 12 Q14 5 20 5 Q26 5 28 12" fill="#07DDE7" stroke="#07DDE7" stroke-width="2"/><circle cx="17" cy="14" r="1.5" fill="#000"/><circle cx="23" cy="14" r="1.5" fill="#000"/></svg>`,
    'tank-03-cain': `<svg viewBox="0 0 40 40" width="32" height="32"><rect x="10" y="8" width="20" height="18" rx="3" fill="#FE6500"/><rect x="14" y="28" width="12" height="8" fill="#FE6500"/><rect x="15" y="13" width="4" height="4" fill="#000"/><rect x="21" y="13" width="4" height="4" fill="#000"/></svg>`,
    'tank-04-abel': `<svg viewBox="0 0 40 40" width="32" height="32"><rect x="10" y="8" width="20" height="18" rx="3" fill="#07CF8D"/><rect x="14" y="28" width="12" height="8" fill="#07CF8D"/><rect x="15" y="13" width="4" height="4" fill="#000"/><rect x="21" y="13" width="4" height="4" fill="#000"/></svg>`,
    'tank-05-juan': `<svg viewBox="0 0 40 40" width="32" height="32"><circle cx="20" cy="15" r="8" fill="#C60B1E"/><path d="M8 35 Q8 25 20 25 Q32 25 32 35" fill="#FFC400"/><circle cx="17" cy="14" r="1.5" fill="#000"/><circle cx="23" cy="14" r="1.5" fill="#000"/></svg>`,
    'tank-06-juanita': `<svg viewBox="0 0 40 40" width="32" height="32"><circle cx="20" cy="15" r="8" fill="#FFC400"/><path d="M8 35 Q8 25 20 25 Q32 25 32 35" fill="#C60B1E"/><path d="M12 12 Q14 5 20 5 Q26 5 28 12" fill="#FFC400"/><circle cx="17" cy="14" r="1.5" fill="#000"/><circle cx="23" cy="14" r="1.5" fill="#000"/></svg>`,
    'tank-07-klaus': `<svg viewBox="0 0 40 40" width="32" height="32"><circle cx="20" cy="15" r="8" fill="#000"/><path d="M8 35 Q8 25 20 25 Q32 25 32 35" fill="#DD0000"/><rect x="8" y="33" width="24" height="4" fill="#FFCC00"/><circle cx="17" cy="14" r="1.5" fill="#fff"/><circle cx="23" cy="14" r="1.5" fill="#fff"/></svg>`,
    'tank-08-genevieve': `<svg viewBox="0 0 40 40" width="32" height="32"><circle cx="20" cy="15" r="8" fill="#DD0000"/><path d="M8 35 Q8 25 20 25 Q32 25 32 35" fill="#FFCC00"/><path d="M12 12 Q14 5 20 5 Q26 5 28 12" fill="#DD0000"/><circle cx="17" cy="14" r="1.5" fill="#000"/><circle cx="23" cy="14" r="1.5" fill="#000"/></svg>`,
    'tank-09-wei': `<svg viewBox="0 0 40 40" width="32" height="32"><circle cx="20" cy="15" r="8" fill="#DE2910"/><path d="M8 35 Q8 25 20 25 Q32 25 32 35" fill="#FFDE00"/><circle cx="17" cy="14" r="1.5" fill="#000"/><circle cx="23" cy="14" r="1.5" fill="#000"/></svg>`,
    'tank-10-mei': `<svg viewBox="0 0 40 40" width="32" height="32"><circle cx="20" cy="15" r="8" fill="#FFDE00"/><path d="M8 35 Q8 25 20 25 Q32 25 32 35" fill="#DE2910"/><path d="M12 12 Q14 5 20 5 Q26 5 28 12" fill="#FFDE00"/><circle cx="17" cy="14" r="1.5" fill="#000"/><circle cx="23" cy="14" r="1.5" fill="#000"/></svg>`,
    'tank-11-haruki': `<svg viewBox="0 0 40 40" width="32" height="32"><circle cx="20" cy="15" r="8" fill="#fff"/><path d="M8 35 Q8 25 20 25 Q32 25 32 35" fill="#BC002D"/><circle cx="20" cy="15" r="4" fill="#BC002D"/><circle cx="17" cy="14" r="1" fill="#000"/><circle cx="23" cy="14" r="1" fill="#000"/></svg>`,
    'tank-12-sakura': `<svg viewBox="0 0 40 40" width="32" height="32"><circle cx="20" cy="15" r="8" fill="#FFB7C5"/><path d="M8 35 Q8 25 20 25 Q32 25 32 35" fill="#BC002D"/><path d="M12 12 Q14 5 20 5 Q26 5 28 12" fill="#FFB7C5"/><circle cx="17" cy="14" r="1.5" fill="#000"/><circle cx="23" cy="14" r="1.5" fill="#000"/></svg>`,
    'tank-13-victor': `<svg viewBox="0 0 40 40" width="32" height="32"><circle cx="20" cy="20" r="12" fill="#07CF8D" opacity="0.3"/><circle cx="20" cy="20" r="8" fill="#07CF8D"/><circle cx="20" cy="20" r="4" fill="#000"/><circle cx="22" cy="18" r="2" fill="#fff"/></svg>`,
    'tank-14-iris': `<svg viewBox="0 0 40 40" width="32" height="32"><circle cx="20" cy="20" r="12" fill="#07DDE7" opacity="0.3"/><circle cx="20" cy="20" r="8" fill="#07DDE7"/><circle cx="20" cy="20" r="4" fill="#000"/><circle cx="22" cy="18" r="2" fill="#fff"/></svg>`,
    'tank-15-observer': `<svg viewBox="0 0 40 40" width="32" height="32"><circle cx="20" cy="20" r="14" fill="none" stroke="#07CF8D" stroke-width="2"/><circle cx="20" cy="20" r="8" fill="none" stroke="#07CF8D" stroke-width="2"/><circle cx="20" cy="20" r="2" fill="#07CF8D"/><line x1="20" y1="6" x2="20" y2="12" stroke="#FE6500" stroke-width="2"/></svg>`,
    'tank-16-seeker': `<svg viewBox="0 0 40 40" width="32" height="32"><circle cx="18" cy="18" r="10" fill="none" stroke="#07DDE7" stroke-width="3"/><line x1="26" y1="26" x2="34" y2="34" stroke="#07DDE7" stroke-width="3" stroke-linecap="round"/><circle cx="18" cy="18" r="4" fill="#07DDE7" opacity="0.3"/></svg>`,
    'tank-17-seth': `<svg viewBox="0 0 40 40" width="32" height="32"><rect x="10" y="8" width="20" height="18" rx="3" fill="#07DDE7"/><rect x="14" y="28" width="12" height="8" fill="#07DDE7"/><rect x="15" y="13" width="4" height="4" fill="#000"/><rect x="21" y="13" width="4" height="4" fill="#000"/></svg>`,
};

async function loadLiveFeed() {
    try {
        const response = await fetch('/data/live-feed.json?' + Date.now());
        if (!response.ok) throw new Error('Feed not found');
        liveFeed = await response.json();
        lastUpdate = new Date(liveFeed.generated_at);
        console.log('[LIVE] Feed loaded:', liveFeed.stats);
        return true;
    } catch (error) {
        console.warn('[LIVE] Using demo mode:', error.message);
        return false;
    }
}

function getTankData(tankId) {
    if (!liveFeed || !liveFeed.tanks[tankId]) return null;
    return liveFeed.tanks[tankId];
}

function getSpecimenSVG(tankId) {
    return SPECIMEN_SVGS[tankId] || SPECIMEN_SVGS['tank-01-adam'];
}

function updateTankPanel(tankId) {
    const data = getTankData(tankId);
    const panel = document.getElementById(tankId);
    if (!panel || !data) return;
    
    const isActive = data.status === 'active';
    const statusEl = panel.querySelector('.tank-status');
    const bodyEl = panel.querySelector('.tank-body');
    const nameEl = panel.querySelector('.tank-name');
    
    // Add SVG avatar next to name
    if (nameEl && !nameEl.querySelector('svg')) {
        nameEl.innerHTML = getSpecimenSVG(tankId) + ' ' + data.name;
    }
    
    if (statusEl) {
        statusEl.className = 'tank-status ' + (isActive ? 'active' : 'sleeping');
        statusEl.textContent = isActive ? 'Active' : 'Quiet';
    }
    
    if (bodyEl && data.recent_thoughts && data.recent_thoughts.length > 0) {
        const latest = data.recent_thoughts[0];
        const thought = latest.thought_en || latest.thought || 'Exploring...';
        const originalThought = latest.thought_en && latest.language !== 'en' ? latest.thought : null;
        const langBadge = latest.language && latest.language !== 'en' ? `<span class="thought-lang-badge">${latest.language.toUpperCase()}</span>` : '';
        
        bodyEl.innerHTML = `
            <div class="tank-article">Reading: <strong>${latest.article || 'Unknown'}</strong>${langBadge}</div>
            <div class="tank-thought">${thought}</div>
            ${originalThought ? `<div class="thought-original">Original: ${originalThought}</div>` : ''}
        `;
        panel.classList.remove('sleeping');
    }
    
    const footer = panel.querySelector('.tank-footer');
    if (footer && data.recent_thoughts && data.recent_thoughts[0]) {
        const latest = data.recent_thoughts[0];
        footer.innerHTML = `<span>${data.type}</span><span>Last: ${latest.date} ${latest.time}</span>`;
    }
}

function updateAllTanks() {
    if (!liveFeed) return;
    Object.keys(liveFeed.tanks).forEach(tankId => {
        updateTankPanel(tankId);
        tankStates[tankId] = liveFeed.tanks[tankId].status === 'active';
    });
}

function updateStats() {
    if (!liveFeed || !liveFeed.stats) return;
    
    const statsEl = document.getElementById('global-stats');
    if (statsEl) {
        const pruneInfo = liveFeed.prune_stats ? ` (${liveFeed.prune_stats.pruned} junk entries pruned)` : '';
        statsEl.innerHTML = `
            <span>📊 ${liveFeed.stats.total_traces.toLocaleString()} traces${pruneInfo}</span>
            <span>🧬 ${liveFeed.stats.total_baselines} baselines</span>
            <span>🐟 ${liveFeed.stats.active_tanks}/17 active</span>
        `;
    }
}

function updateNextRefresh() {
    if (!liveFeed) return;
    const nextEl = document.getElementById('next-update');
    if (nextEl) {
        nextEl.innerHTML = `
            <strong>12-Hour Delayed Relay</strong> • Next update: ${liveFeed.next_update}<br>
            <span style="font-size: 0.75rem; color: var(--gray);">
                Captured by THE BROADCASTER • Coordinated with THE SCHEDULER, THE CARETAKER, THE WEBMASTER<br>
                Full logs: <a href="mailto:research@digiquarium.org" style="color: var(--cyan);">research@digiquarium.org</a>
            </span>
        `;
    }
}

function openFullscreenWithData(tankId) {
    const data = getTankData(tankId);
    if (!data) {
        if (typeof originalOpenFullscreen === 'function') originalOpenFullscreen(tankId);
        return;
    }
    
    const overlay = document.getElementById('fullscreen');
    overlay.style.display = 'flex';
    
    document.getElementById('fs-name').innerHTML = getSpecimenSVG(tankId) + ' ' + data.name;
    document.getElementById('fs-status').textContent = data.status === 'active' ? '● Active' : '○ Quiet';
    
    const thoughtsEl = document.getElementById('fs-thoughts');
    if (data.recent_thoughts && data.recent_thoughts.length > 0) {
        thoughtsEl.innerHTML = data.recent_thoughts.map(t => `
            <div class="thought-entry" style="margin-bottom: 15px; padding: 15px; background: rgba(0,0,0,0.3); border-radius: 8px;">
                <div style="color: var(--cyan); font-size: 0.8rem; margin-bottom: 5px;">
                    ${t.date} ${t.time} • ${t.article}
                </div>
                <div style="color: var(--white);">${t.thought || 'Exploring ' + t.article + '...'}</div>
                ${t.next ? `<div style="color: var(--gray); font-size: 0.8rem; margin-top: 5px;">→ Next: ${t.next}</div>` : ''}
            </div>
        `).join('');
    }
    
    document.getElementById('fs-traces').textContent = data.traces_12h || 0;
    document.getElementById('fs-baselines').textContent = data.latest_baseline ? data.latest_baseline.number : '0';
    
    if (data.recent_thoughts && data.recent_thoughts[0]) {
        document.getElementById('fs-article').textContent = data.recent_thoughts[0].article;
    }
    
    const pathEl = document.getElementById('fs-path');
    if (data.top_topics && data.top_topics.length > 0) {
        pathEl.innerHTML = '<strong>Top Topics:</strong><br>' + 
            data.top_topics.map(t => `${t.topic} (${t.visits})`).join(' → ');
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    const loaded = await loadLiveFeed();
    
    if (loaded) {
        console.log('[LIVE] Updating tanks with real data');
        updateAllTanks();
        updateStats();
        updateNextRefresh();
        window.originalOpenFullscreen = window.openFullscreen;
        window.openFullscreen = openFullscreenWithData;
    }
    
    if (typeof renderTanks === 'function') {
        renderTanks();
        if (loaded) setTimeout(updateAllTanks, 100);
    }
});
