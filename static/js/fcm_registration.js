/**
 * FCM Token Registration for NeuroLearn
 * Handles permission request, token retrieval, and registration with Django backend.
 */

async function registerFCM() {
    try {
        // 1. Request Permission
        const permission = await Notification.requestPermission();
        if (permission !== 'granted') {
            console.warn('Notification permission denied.');
            return;
        }

        // 2. Get FCM Token
        // This assumes Firebase has been initialized in your main app
        // const messaging = firebase.messaging();
        // const currentToken = await messaging.getToken({ vapidKey: 'YOUR_VAPID_KEY' });

        // Dummy implementation for structure (User must replace with actual Firebase config)
        if (typeof firebase !== 'undefined' && firebase.messaging) {
            const messaging = firebase.messaging();
            messaging.getToken({ vapidKey: 'YOUR_PUBLIC_VAPID_KEY' })
                .then((currentToken) => {
                    if (currentToken) {
                        console.log('FCM Token retrieved:', currentToken);
                        sendTokenToBackend(currentToken);
                    } else {
                        console.warn('No registration token available. Request permission to generate one.');
                    }
                })
                .catch((err) => {
                    console.error('An error occurred while retrieving token. ', err);
                });
        }

    } catch (error) {
        console.error('FCM Registration failed:', error);
    }
}

async function sendTokenToBackend(token) {
    const csrftoken = getCookie('csrftoken');

    try {
        const response = await fetch('/api/fcm-token/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({
                fcm_token: token,
                device_id: navigator.userAgent // Optional: use UA as device ID
            })
        });

        if (response.ok) {
            console.log('FCM token registered successfully with NeuroLearn backend.');
        } else {
            const error = await response.json();
            console.error('Failed to register FCM token:', error);
        }
    } catch (error) {
        console.error('Error sending token to backend:', error);
    }
}

// Utility to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Call on page load or after login
// window.addEventListener('load', registerFCM);
