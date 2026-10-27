// AAC Shared Logic (State Management)

// Initialize sentence from LocalStorage or empty array
let sentence = JSON.parse(localStorage.getItem('aac_sentence') || '[]');

document.addEventListener('DOMContentLoaded', () => {
    updateStrip(); // Render on load
});

function selectSymbol(word, imageUrl, color) {
    // Speak immediately
    speak(word);

    // Add to sentence (Unlimited)
    sentence.push({
        word: word,
        color: color
    });

    saveState();
    updateStrip();
}

function updateStrip() {
    const container = document.getElementById('sentence-container');
    if (!container) return; // Guard for pages without the strip

    container.innerHTML = ''; // Clear current

    sentence.forEach((item, index) => {
        const slot = document.createElement('div');
        slot.className = 'sentence-slot';
        slot.style.borderStyle = 'solid';

        // Color coding
        if (item.color === 'yellow') slot.style.borderColor = 'var(--color-noun)';
        else if (item.color === 'green') slot.style.borderColor = 'var(--color-verb)';
        else if (item.color === 'blue') slot.style.borderColor = 'var(--color-adj)';
        else if (item.color === 'red') slot.style.borderColor = '#ef4444';
        else slot.style.borderColor = 'var(--color-highlight)';

        slot.style.background = 'white';
        slot.style.position = 'relative'; // Ensure positioning context

        // Add word
        slot.innerHTML = `<span style='font-weight:700;'>${item.word}</span>`;

        // Add remove icon (small cross at top right)
        const cross = document.createElement('span');
        cross.className = 'material-icons';
        cross.style.fontSize = '14px';
        cross.style.position = 'absolute';
        cross.style.top = '2px';
        cross.style.right = '2px';
        cross.style.color = '#ef4444';
        cross.innerText = 'close';
        slot.appendChild(cross);

        // Add remove functionality on click
        slot.onclick = () => removeWord(index);
        slot.style.cursor = 'pointer';

        container.appendChild(slot);
    });

    // Auto-scroll to end
    container.scrollLeft = container.scrollWidth;
}

function removeWord(index) {
    sentence.splice(index, 1);
    saveState();
    updateStrip();
}

function clearSentence() {
    sentence = [];
    saveState();
    updateStrip();
}

function speakSentence() {
    if (sentence.length > 0) {
        const words = sentence.map(s => s.word).join(" ");
        speak(words);
    } else {
        // Optional feedback
    }
}

function saveState() {
    localStorage.setItem('aac_sentence', JSON.stringify(sentence));
}

// Integrated Type Support
function addTypedWord() {
    const input = document.getElementById('strip-type-input');
    if (!input) return;

    const word = input.value.trim();
    if (word) {
        selectSymbol(word, null, 'highlight');
        input.value = '';
        input.focus();
    }
}

// Global listener for the integrated input
document.addEventListener('keypress', (e) => {
    const input = document.getElementById('strip-type-input');
    if (input && document.activeElement === input && e.key === 'Enter') {
        addTypedWord();
    }
});
