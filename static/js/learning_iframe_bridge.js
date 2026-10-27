/**
 * Learning Iframe Bridge
 * 
 * This script listens for completion messages from interactive learning modules
 * (Figma prototypes) and saves the progress to the NeuroLearn backend.
 */

(function () {
    // Utility to get CSRF token from cookies
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

    // Function to save progress via the API
    async function saveLearningProgress(module, item, completed = true) {
        console.log(`[NeuroLearn] Saving progress for ${module}: ${item}`);

        try {
            const response = await fetch('/learning/api/complete/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    module: module,
                    item: String(item),
                    completed: completed
                })
            });

            if (response.ok) {
                const result = await response.json();
                console.log('[NeuroLearn] Progress saved successfully:', result);

                // Optional: Show a small toast or notification if we want
                if (window.showToast) {
                    window.showToast(`Mastered: ${item}!`, 'success');
                }
            } else {
                const error = await response.json();
                console.error('[NeuroLearn] Failed to save progress:', error);
            }
        } catch (err) {
            console.error('[NeuroLearn] Error communicating with backend:', err);
        }
    }

    // Function to send current progress to the iframe
    function sendProgressToIframe() {
        const iframe = document.querySelector('iframe');
        if (iframe && iframe.contentWindow && window.COMPLETED_ITEMS) {
            console.log('[NeuroLearn] Sending progress to iframe:', window.COMPLETED_ITEMS);
            iframe.contentWindow.postMessage({
                type: 'restore_progress',
                module: window.CURRENT_LEARNING_MODULE,
                completed_items: window.COMPLETED_ITEMS
            }, '*');
        }
    }

    // Listen for messages from the iframe
    window.addEventListener('message', function (event) {
        const data = event.data;

        // Handle various message formats that might come from prototypes
        // 1. Standard format: { type: 'complete', module: 'numbers', item: '5' }
        // 2. Simple format: { type: 'learning_complete', item: 'A' }

        if (data && (data.type === 'complete' || data.type === 'learning_complete' || data.action === 'complete')) {
            const module = data.module || window.CURRENT_LEARNING_MODULE;
            const item = data.item || data.value;

            if (module && item) {
                saveLearningProgress(module, item);
            }
        }

        // If the prototype asks for progress
        if (data && (data.type === 'get_progress' || data.action === 'get_progress')) {
            sendProgressToIframe();
        }
    });

    // Send progress when iframe finishes loading
    const iframe = document.querySelector('iframe');
    if (iframe) {
        iframe.addEventListener('load', function () {
            // Small delay to ensure prototype is ready to listen
            setTimeout(sendProgressToIframe, 1000);
        });
    }

    // Handle events from specific custom prototypes if needed
    window.addEventListener('neurolearn_complete', function (e) {
        if (e.detail && e.detail.item) {
            const module = e.detail.module || window.CURRENT_LEARNING_MODULE;
            saveLearningProgress(module, e.detail.item);
        }
    });

    console.log('[NeuroLearn] Learning bridge initialized.');
})();
