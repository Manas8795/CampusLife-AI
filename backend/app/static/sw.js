// CampusLife AI — Progressive Web App Service Worker
const CACHE_NAME = 'campuslife-pwa-v2';
const STATIC_ASSETS = [
  '/',
  '/call',
  '/static/manifest.json',
  '/static/icon.svg',
  '/static/shared-shell.css',
  '/static/shared-shell.js',
  '/voice/ringtone.wav'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.warn('[SW] Caching failed for some static assets:', err);
      });
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((k) => {
          if (k !== CACHE_NAME) {
            return caches.delete(k);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Network-first with Cache fallback strategy
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);

  // Skip dynamic API calls and WebSockets from cache
  if (url.pathname.startsWith('/api') || url.pathname.startsWith('/ws') || url.pathname.startsWith('/voice/tts')) {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (response && response.status === 200) {
          const respClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, respClone);
          });
        }
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});

// Native Web Push notifications with tactile vibration alerts
self.addEventListener('push', (event) => {
  let data = {
    title: 'CampusLife AI Sentinel',
    body: 'Urgent academic alert: You have an upcoming deadline.',
    icon: '/static/icon.svg',
    badge: '/static/icon.svg',
    vibrate: [250, 100, 250, 100, 400],
    data: { url: '/call' },
    actions: [
      { action: 'call_ai', title: '🎙️ Call AI Mentor' },
      { action: 'view_tasks', title: '📋 Open Tasks' }
    ]
  };

  if (event.data) {
    try {
      const parsed = event.data.json();
      data = { ...data, ...parsed };
    } catch (e) {
      data.body = event.data.text();
    }
  }

  event.waitUntil(
    self.registration.showNotification(data.title, data)
  );
});

// Interactive notification click handling
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const targetUrl = event.action === 'view_tasks' ? '/#study' : '/call';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
      for (let client of windowClients) {
        if (client.url.includes(targetUrl) && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
    })
  );
});
