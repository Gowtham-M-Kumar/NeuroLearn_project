// WebRTC Video Call Script — WhatsApp-Style Call Flow
// Flow: call-request → incoming popup → accept/reject → WebRTC offer/answer

let localStream;
let peerConnection;
let signalingSocket;

const localVideo = document.getElementById('local-video');
const remoteVideo = document.getElementById('remote-video');
const videoModal = document.getElementById('video-call-modal');
const outgoingModal = document.getElementById('outgoing-call-modal');
const incomingModal = document.getElementById('incoming-call-modal');
const endCallBtn = document.getElementById('end-call-btn');
const toggleMicBtn = document.getElementById('toggle-mic-btn');
const toggleVidBtn = document.getElementById('toggle-vid-btn');
const cancelCallBtn = document.getElementById('cancel-call-btn');
const acceptCallBtn = document.getElementById('accept-call-btn');
const rejectCallBtn = document.getElementById('reject-call-btn');
const ringtoneAudio = document.getElementById('ringtone-audio');

let isMicMuted = false;
let isVidOff = false;
let callState = 'idle'; // idle | outgoing | incoming | active
let ringTimeout = null;
let iceCandidatesQueue = [];
let isGettingMedia = false;

// STUN servers
const rtcConfig = {
    iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' },
        { urls: 'stun:stun2.l.google.com:19302' },
        { urls: 'stun:stun3.l.google.com:19302' }
    ]
};

// ===================== SIGNALING =====================

function initSignaling(otherUserId) {
    if (signalingSocket && (signalingSocket.readyState === WebSocket.OPEN || signalingSocket.readyState === WebSocket.CONNECTING)) return;

    const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const wsUrl = `${protocol}${window.location.host}/ws/call/${otherUserId}/`;

    console.log('[WebRTC] Connecting to signaling at', wsUrl);
    signalingSocket = new WebSocket(wsUrl);

    signalingSocket.onmessage = async (e) => {
        const data = JSON.parse(e.data);
        const type = data.type;
        console.log('[WebRTC] Received signal:', type);

        switch (type) {
            case 'call-request':
                handleIncomingCallRequest(data);
                break;
            case 'call-accepted':
                handleCallAccepted();
                break;
            case 'call-rejected':
                handleCallRejected();
                break;
            case 'call-cancelled':
                handleCallCancelled();
                break;
            case 'call-ended':
                handleCallEnded();
                break;
            case 'offer':
                await handleOffer(data.offer);
                break;
            case 'answer':
                await handleAnswer(data.answer);
                break;
            case 'candidate':
                await handleCandidate(data.candidate);
                break;
            case 'media-status':
                handleRemoteMediaStatus(data.media, data.enabled);
                break;
        }
    };

    signalingSocket.onopen = () => console.log('[WebRTC] Signaling connected');
    signalingSocket.onclose = () => {
        console.log('[WebRTC] Signaling disconnected');
        if (callState === 'active') {
            console.warn('[WebRTC] Signaling lost during active call');
        }
    };
    signalingSocket.onerror = (err) => console.error('[WebRTC] Signaling error:', err);
}

function sendSignal(data) {
    if (signalingSocket && signalingSocket.readyState === WebSocket.OPEN) {
        signalingSocket.send(JSON.stringify(data));
    } else {
        console.warn('[WebRTC] Cannot send signal, socket not open:', data.type);
    }
}

// ===================== CALL FLOW =====================

async function getUserMediaStream() {
    if (localStream) return localStream;
    if (isGettingMedia) {
        // Wait until existing request finishes
        return new Promise((resolve) => {
            const checkInterval = setInterval(() => {
                if (!isGettingMedia) {
                    clearInterval(checkInterval);
                    resolve(localStream);
                }
            }, 100);
        });
    }

    isGettingMedia = true;
    try {
        console.log('[WebRTC] Requesting media devices...');
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        localStream = stream;
        if (localVideo) localVideo.srcObject = stream;
        return stream;
    } finally {
        isGettingMedia = false;
    }
}

// STEP 1: Caller clicks "Video Call" → sends call-request
async function startVideoCall(otherUserId) {
    if (callState !== 'idle') {
        console.log('[WebRTC] Already in a call state:', callState);
        return;
    }

    // Ensure signaling is open
    if (!signalingSocket || signalingSocket.readyState !== WebSocket.OPEN) {
        initSignaling(otherUserId);
        await new Promise(resolve => {
            const onOpen = () => {
                signalingSocket.removeEventListener('open', onOpen);
                resolve();
            };
            signalingSocket.addEventListener('open', onOpen);
        });
    }

    callState = 'outgoing';
    showOutgoingCallScreen();

    // Send call request to remote
    sendSignal({ type: 'call-request' });

    // Auto-cancel call after 45 seconds if no response
    ringTimeout = setTimeout(() => {
        if (callState === 'outgoing') {
            sendSignal({ type: 'call-cancelled' });
            hideOutgoingCallScreen();
            callState = 'idle';
            alert('No answer. The call was not picked up.');
        }
    }, 45000);
}

// STEP 2: Receiver gets call-request → show incoming call popup
function handleIncomingCallRequest(data) {
    if (callState !== 'idle') {
        // Already busy, auto-reject
        console.log('[WebRTC] Busy, auto-rejecting call request');
        sendSignal({ type: 'call-rejected' });
        return;
    }

    callState = 'incoming';
    showIncomingCallScreen();
    playRingtone();
}

// STEP 3a: Receiver clicks "Accept" → Get media FIRST, then send call-accepted
async function acceptCall() {
    stopRingtone();
    hideIncomingCallScreen();

    console.log('[WebRTC] Accepting call, getting media first...');
    
    // Set active early to block other incoming requests
    callState = 'active'; 

    try {
        const stream = await getUserMediaStream();
        if (!stream) throw new Error('No stream obtained');
        
        console.log('[WebRTC] Media ready, sending call-accepted');
        sendSignal({ type: 'call-accepted' });
        showVideoCallModal();
    } catch (err) {
        console.error("[WebRTC] Error accessing media devices.", err);
        alert("Could not access camera/microphone.");
        callState = 'idle';
        sendSignal({ type: 'call-rejected' }); // Tell caller we failed
        return;
    }
}

// STEP 3b: Receiver clicks "Reject" → sends call-rejected
function rejectCall() {
    stopRingtone();
    hideIncomingCallScreen();
    callState = 'idle';
    sendSignal({ type: 'call-rejected' });
}

// STEP 4: Caller receives call-accepted → get media, create offer
async function handleCallAccepted() {
    if (callState !== 'outgoing') return;

    clearTimeout(ringTimeout);
    hideOutgoingCallScreen();
    callState = 'active';

    console.log('[WebRTC] Call accepted by remote, preparing offer...');

    try {
        const stream = await getUserMediaStream();
        if (!stream) throw new Error('No stream obtained');

        showVideoCallModal();
        createPeerConnection();

        // Add tracks
        stream.getTracks().forEach(track => {
            peerConnection.addTrack(track, stream);
        });

        // Create and send offer
        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);
        console.log('[WebRTC] Sending offer');
        sendSignal({ type: 'offer', offer: offer });
    } catch (err) {
        console.error("[WebRTC] Error in handleCallAccepted:", err);
        alert("Call setup failed.");
        endCall();
    }
}

// Caller receives rejection
function handleCallRejected() {
    clearTimeout(ringTimeout);
    hideOutgoingCallScreen();
    callState = 'idle';
    alert('Call was declined.');
}

// Receiver: Caller cancelled before pickup
function handleCallCancelled() {
    stopRingtone();
    hideIncomingCallScreen();
    callState = 'idle';
}

// Remote user ended the active call
function handleCallEnded() {
    console.log('[WebRTC] Remote ended call');
    closeVideoCallModal();
}

// ===================== WEBRTC HANDLERS =====================

async function handleOffer(offer) {
    console.log('[WebRTC] Handling offer...');
    
    try {
        const stream = await getUserMediaStream();
        if (!stream) throw new Error('No stream obtained');

        createPeerConnection();

        stream.getTracks().forEach(track => {
            peerConnection.addTrack(track, stream);
        });

        await peerConnection.setRemoteDescription(new RTCSessionDescription(offer));
        console.log('[WebRTC] Remote description set (offer)');

        const answer = await peerConnection.createAnswer();
        await peerConnection.setLocalDescription(answer);
        console.log('[WebRTC] Sending answer');
        sendSignal({ type: 'answer', answer: answer });

        // Process any queued candidates now that remote description is set
        processQueuedCandidates();
    } catch (err) {
        console.error('[WebRTC] Error in handleOffer:', err);
        endCall();
    }
}

async function handleAnswer(answer) {
    console.log('[WebRTC] Handling answer...');
    if (peerConnection) {
        try {
            await peerConnection.setRemoteDescription(new RTCSessionDescription(answer));
            console.log('[WebRTC] Remote description set (answer)');
            processQueuedCandidates();
        } catch (err) {
            console.error('[WebRTC] Error setting answer:', err);
        }
    }
}

async function handleCandidate(candidate) {
    if (peerConnection && peerConnection.remoteDescription) {
        try {
            await peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
        } catch (err) {
            console.error('[WebRTC] Error adding received candidate:', err);
        }
    } else {
        console.log('[WebRTC] Queuing candidate, peer connection not ready');
        iceCandidatesQueue.push(candidate);
    }
}

function processQueuedCandidates() {
    if (!peerConnection || !peerConnection.remoteDescription) return;
    
    console.log(`[WebRTC] Processing ${iceCandidatesQueue.length} queued candidates`);
    while (iceCandidatesQueue.length > 0) {
        const candidate = iceCandidatesQueue.shift();
        peerConnection.addIceCandidate(new RTCIceCandidate(candidate))
            .catch(e => console.error('[WebRTC] Error processing queued candidate:', e));
    }
}

function createPeerConnection() {
    if (peerConnection) return;

    console.log('[WebRTC] Creating RTCPeerConnection');
    peerConnection = new RTCPeerConnection(rtcConfig);

    peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
            sendSignal({ type: 'candidate', candidate: event.candidate });
        }
    };

    peerConnection.ontrack = (event) => {
        console.log('[WebRTC] OnTrack received remote stream');
        if (remoteVideo) {
            remoteVideo.srcObject = event.streams[0];
            remoteVideo.style.display = 'block';
            const rp = document.getElementById('remote-placeholder');
            if (rp) rp.style.display = 'none';
        }
    };

    peerConnection.oniceconnectionstatechange = () => {
        console.log('[WebRTC] ICE Connection state:', peerConnection.iceConnectionState);
        if (peerConnection.iceConnectionState === 'failed') {
            console.error('[WebRTC] ICE Connection failed');
            // Try to restart ICE or end call
            // For now, just end
            closeVideoCallModal();
        }
    };

    peerConnection.onconnectionstatechange = () => {
        const state = peerConnection.connectionState;
        console.log('[WebRTC] Connection state:', state);
        if (state === 'disconnected' || state === 'failed' || state === 'closed') {
            closeVideoCallModal();
        }
    };
}

function handleRemoteMediaStatus(media, enabled) {
    if (media === 'video') {
        if (remoteVideo) {
            remoteVideo.style.display = enabled ? 'block' : 'none';
        }
        const rp = document.getElementById('remote-placeholder');
        if (rp) {
            rp.style.display = enabled ? 'none' : 'flex';
        }
    }
}

// ===================== UI MODALS =====================

function showOutgoingCallScreen() {
    if (outgoingModal) outgoingModal.style.display = 'flex';
    const statusEl = document.getElementById('outgoing-call-status');
    if (statusEl) statusEl.textContent = 'Calling...';
}

function hideOutgoingCallScreen() {
    if (outgoingModal) outgoingModal.style.display = 'none';
}

function showIncomingCallScreen() {
    if (incomingModal) incomingModal.style.display = 'flex';
}

function hideIncomingCallScreen() {
    if (incomingModal) incomingModal.style.display = 'none';
}

function showVideoCallModal() {
    if (videoModal) videoModal.style.display = 'flex';

    // Reset toggle states
    isMicMuted = false;
    isVidOff = false;
    if (toggleMicBtn) {
        toggleMicBtn.classList.remove('off');
        const icon = toggleMicBtn.querySelector('.material-icons');
        if (icon) icon.innerText = 'mic';
    }
    if (toggleVidBtn) {
        toggleVidBtn.classList.remove('off');
        const icon = toggleVidBtn.querySelector('.material-icons');
        if (icon) icon.innerText = 'videocam';
    }

    // Reset placeholders
    if (localVideo) localVideo.style.display = 'block';
    const lp = document.getElementById('local-placeholder');
    if (lp) lp.style.display = 'none';
    
    if (remoteVideo) remoteVideo.style.display = 'block';
    const rp = document.getElementById('remote-placeholder');
    if (rp) rp.style.display = 'none';
}

function closeVideoCallModal() {
    if (videoModal) videoModal.style.display = 'none';
    endCall();
}

function endCall() {
    // Notify remote if we were in an active session
    if (callState === 'active' || callState === 'outgoing') {
        sendSignal({ type: 'call-ended' });
    }

    if (localStream) {
        localStream.getTracks().forEach(track => {
            track.stop();
            console.log(`[WebRTC] Track ${track.kind} stopped`);
        });
        localStream = null;
    }

    if (peerConnection) {
        peerConnection.onicecandidate = null;
        peerConnection.ontrack = null;
        peerConnection.close();
        peerConnection = null;
        console.log('[WebRTC] PeerConnection closed');
    }

    if (remoteVideo) remoteVideo.srcObject = null;
    if (localVideo) localVideo.srcObject = null;

    iceCandidatesQueue = [];
    callState = 'idle';
}

// ===================== RINGTONE =====================

function playRingtone() {
    if (ringtoneAudio) {
        ringtoneAudio.currentTime = 0;
        ringtoneAudio.play().catch(e => console.log('[WebRTC] Ringtone play blocked by browser policy'));
    }
}

function stopRingtone() {
    if (ringtoneAudio) {
        ringtoneAudio.pause();
        ringtoneAudio.currentTime = 0;
    }
}

// ===================== BUTTON HANDLERS =====================

if (endCallBtn) endCallBtn.addEventListener('click', closeVideoCallModal);

if (cancelCallBtn) {
    cancelCallBtn.addEventListener('click', () => {
        clearTimeout(ringTimeout);
        sendSignal({ type: 'call-cancelled' });
        hideOutgoingCallScreen();
        callState = 'idle';
    });
}

if (acceptCallBtn) acceptCallBtn.addEventListener('click', acceptCall);
if (rejectCallBtn) rejectCallBtn.addEventListener('click', rejectCall);

if (toggleMicBtn) {
    toggleMicBtn.addEventListener('click', () => {
        if (!localStream) return;
        isMicMuted = !isMicMuted;
        localStream.getAudioTracks().forEach(track => track.enabled = !isMicMuted);
        toggleMicBtn.classList.toggle('off', isMicMuted);
        const icon = toggleMicBtn.querySelector('.material-icons');
        if (icon) icon.innerText = isMicMuted ? 'mic_off' : 'mic';
        sendSignal({ type: 'media-status', media: 'audio', enabled: !isMicMuted });
    });
}

if (toggleVidBtn) {
    toggleVidBtn.addEventListener('click', () => {
        if (!localStream) return;
        isVidOff = !isVidOff;
        localStream.getVideoTracks().forEach(track => track.enabled = !isVidOff);
        
        if (localVideo) localVideo.style.display = isVidOff ? 'none' : 'block';
        const lp = document.getElementById('local-placeholder');
        if (lp) lp.style.display = isVidOff ? 'flex' : 'none';

        toggleVidBtn.classList.toggle('off', isVidOff);
        const icon = toggleVidBtn.querySelector('.material-icons');
        if (icon) icon.innerText = isVidOff ? 'videocam_off' : 'videocam';
        sendSignal({ type: 'media-status', media: 'video', enabled: !isVidOff });
    });
}

// ===================== INIT SIGNALING ON PAGE LOAD =====================

document.addEventListener('DOMContentLoaded', () => {
    if (typeof otherUserId !== 'undefined') {
        initSignaling(otherUserId);
    } else {
        console.warn('[WebRTC] otherUserId not found in global scope');
    }
});
