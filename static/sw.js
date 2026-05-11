self.addEventListener('push', function(event) {
    const data = event.data ? event.data.json() : {};
    event.waitUntil(
        self.registration.showNotification(data.title || 'New Booking!', {
            body: data.body || 'A new ride request is waiting.',
            icon: '/static/images/car.png',
            badge: '/static/images/car.png',
            vibrate: [300, 100, 300, 100, 300],
            requireInteraction: true,
            tag: 'new-booking'
        })
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    event.waitUntil(clients.openWindow('/'));
});
