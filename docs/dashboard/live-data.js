/**
 * LIVE DATA LOADER
 * Fetches data from /data/live-feed.json (updated every 12 hours by THE BROADCASTER)
 */

let liveFeed = null;
let lastUpdate = null;

async function loadLiveFeed() {
    try {
        const response = await fetch('/thedigiquarium/data/live-feed.json?' + Date.now());
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

function updateTankPanel(tankId) {
    const data = getTankData(tankId);
    const panel = document.getElementById(tankId);
    if (!panel || !data) return;
    
    const isActive = data.status === 'active';
    const statusEl = panel.querySelector('.tank-status');
    const bodyEl = panel.querySelector('.tank-body');
    
    // Update status
    if (statusEl) {
        statusEl.className = 'tank-status ' + (isActive ? 'active' : 'sleeping');
        statusEl.textContent = isActive ? 'Active' : 'Quiet';
    }
    
    // Update body content
    if (bodyEl && data.recent_thoughts && data.recent_thoughts.length > 0) {
        const latest = data.recent_thoughts[0];
        const thought = latest.thought || 'Exploring...';
        
        bodyEl.innerHTML = `
            <div class="tank-article">Reading: <strong>${latest.article || 'Unknown'}</strong></div>
            <div class="tank-thought">${thought}</div>
        `;
        
        // Remove sleeping class
        panel.classList.remove('sleeping');
    }
    
    // Update footer with last activity time
    const footer = panel.querySelector('.tank-footer');
    if (footer && data.recent_thoughts && data.recent_thoughts[0]) {
        const latest = data.recent_thoughts[0];
        footer.innerHTML = `
            <span>${data.type}</span>
            <span>Last: ${latest.date} ${latest.time}</span>
        `;
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
    
    // Update any stats displays
    const statsEl = document.getElementById('global-stats');
    if (statsEl) {
        statsEl.innerHTML = `
            <span>📊 ${liveFeed.stats.total_traces.toLocaleString()} traces</span>
            <span>🧬 ${liveFeed.stats.total_baselines} baselines</span>
            <span>🐟 ${liveFeed.stats.active_tanks}/17 active</span>
        `;
    }
}

function updateNextRefresh() {
    if (!liveFeed) return;
    
    const nextEl = document.getElementById('next-update');
    if (nextEl) {
        nextEl.textContent = `Next update: ${liveFeed.next_update}`;
    }
}

// Enhanced fullscreen view with real data
function openFullscreenWithData(tankId) {
    const data = getTankData(tankId);
    if (!data) {
        openFullscreen(tankId); // Fall back to original
        return;
    }
    
    const overlay = document.getElementById('fullscreen');
    overlay.style.display = 'flex';
    
    document.getElementById('fs-name').textContent = data.name;
    document.getElementById('fs-status').textContent = data.status === 'active' ? '● Active' : '○ Quiet';
    
    // Recent thoughts
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
    
    // Stats
    document.getElementById('fs-traces').textContent = data.traces_12h || 0;
    document.getElementById('fs-baselines').textContent = data.latest_baseline ? data.latest_baseline.number : '0';
    
    // Current article
    if (data.recent_thoughts && data.recent_thoughts[0]) {
        document.getElementById('fs-article').textContent = data.recent_thoughts[0].article;
    }
    
    // Top topics as path
    const pathEl = document.getElementById('fs-path');
    if (data.top_topics && data.top_topics.length > 0) {
        pathEl.innerHTML = '<strong>Top Topics:</strong><br>' + 
            data.top_topics.map(t => `${t.topic} (${t.visits})`).join(' → ');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    const loaded = await loadLiveFeed();
    
    if (loaded) {
        console.log('[LIVE] Updating tanks with real data');
        updateAllTanks();
        updateStats();
        updateNextRefresh();
        
        // Override fullscreen function to use real data
        window.originalOpenFullscreen = window.openFullscreen;
        window.openFullscreen = openFullscreenWithData;
    }
    
    // Re-render with correct active states
    if (typeof renderTanks === 'function') {
        renderTanks();
        if (loaded) updateAllTanks();
    }
});
