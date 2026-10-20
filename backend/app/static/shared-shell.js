// ==========================================================================
// CampusLife AI — Unified Shared Shell Controller & Theme State
// Used across all pages: Dashboard, Study, Health, Expenses, Travel, Intelligence, Voice, Infra
// ==========================================================================

const API_AUTH_HEADERS = {
  'Authorization': 'Bearer user_1',
  'Content-Type': 'application/json'
};

// 1. Sidebar Toggle
function toggleSidebar() {
  document.body.classList.toggle('sidebar-closed');
  const isClosed = document.body.classList.contains('sidebar-closed');
  localStorage.setItem('campuslife_sidebar_closed', isClosed ? 'true' : 'false');
  showToast(isClosed ? 'Navigation bar closed' : 'Navigation bar opened', isClosed ? '◀' : '▶');
}

// Keyboard shortcut: Ctrl+B / Cmd+B
window.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') {
    e.preventDefault();
    toggleSidebar();
  }
});

// 2. Multi-Theme Switcher
function switchTheme(themeKey, elem, label) {
  document.documentElement.setAttribute('data-theme', themeKey);
  const lbl = document.getElementById('themeLabel');
  if (lbl && label) lbl.innerText = label;

  document.querySelectorAll('.swatch-btn').forEach(b => b.classList.remove('active'));
  if (elem) {
    elem.classList.add('active');
  } else {
    const matched = document.querySelector(`.swatch-btn[onclick*="${themeKey}"]`);
    if (matched) matched.classList.add('active');
  }

  localStorage.setItem('campuslife_theme', themeKey);
  window.dispatchEvent(new CustomEvent('campuslife:themechange', { detail: { theme: themeKey } }));
  showToast(`Switched to ${label || themeKey} theme`, '🎨');
}

// 3. Toast Notifications
function showToast(msg, icon = '✅') {
  let toast = document.getElementById('actionToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'actionToast';
    toast.innerHTML = `<span id="toastIcon">${icon}</span> <span id="toastMsg">${msg}</span>`;
    document.body.appendChild(toast);
  } else {
    const m = document.getElementById('toastMsg');
    const ic = document.getElementById('toastIcon');
    if (m) m.innerText = msg;
    if (ic) ic.innerText = icon;
  }
  toast.style.display = 'flex';
  setTimeout(() => { toast.style.display = 'none'; }, 3200);
}

// 3.1 Automatic GSAP Card Entrance Choreography
function triggerShellGSAPEntrance() {
  if (window.gsap) {
    gsap.from(".card, .canvas-3d-card", {
      y: 22,
      opacity: 0,
      stagger: 0.08,
      duration: 0.55,
      ease: "power2.out",
      clearProps: "transform,opacity"
    });
    gsap.from(".welcome-header", {
      y: -15,
      opacity: 0,
      duration: 0.5,
      ease: "power2.out",
      clearProps: "transform,opacity"
    });
  }
}
window.addEventListener('DOMContentLoaded', () => {
  setTimeout(triggerShellGSAPEntrance, 80);
});

// 4. Proactive Call Action
async function triggerImmediateCall() {
  showToast('Broadcasting proactive intervention call...', '📞');
  try {
    const res = await fetch('/api/voice/calls/mobile-ring', {
      method: 'POST',
      headers: API_AUTH_HEADERS,
      body: JSON.stringify({
        greeting: "Hello! This is your CampusLife student co-pilot checking in on your current tasks and academic progress."
      })
    });
    const data = await res.json();
    if (data.phones_ringing > 0) {
      showToast(`Ringing ${data.phones_ringing} connected phone(s)!`, '🔔');
    } else {
      showToast('Call signal active! Open Phone Standby (/call) to answer.', '📲');
    }
  } catch(e) {
    showToast('Error broadcasting call signal.', '✕');
  }
}

// 5. Restore Saved Preferences on Load
(function initSavedPreferences() {
  if (localStorage.getItem('campuslife_sidebar_closed') === 'true') {
    document.body.classList.add('sidebar-closed');
  }
  
  const savedTheme = localStorage.getItem('campuslife_theme') || 'alabaster';
  document.documentElement.setAttribute('data-theme', savedTheme);

  window.addEventListener('DOMContentLoaded', () => {
    const labelMap = {
      alabaster: 'Alabaster',
      nordic: 'Nordic Frost',
      sakura: 'Sakura',
      matcha: 'Matcha',
      latte: 'Latte',
      midnight: 'Midnight',
      cyberpunk: 'Cyberpunk',
      emerald: 'Emerald',
      solar: 'Solar'
    };
    const lbl = document.getElementById('themeLabel');
    if (lbl) lbl.innerText = labelMap[savedTheme] || 'Alabaster';

    document.querySelectorAll('.swatch-btn').forEach(b => b.classList.remove('active'));
    const activeSwatch = document.querySelector(`.swatch-btn[onclick*="${savedTheme}"]`);
    if (activeSwatch) activeSwatch.classList.add('active');
  });
})();
