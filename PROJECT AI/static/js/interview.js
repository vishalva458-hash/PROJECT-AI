// Interview session page interactions: Speech recognition, timer & word counter
document.addEventListener('DOMContentLoaded', () => {
    const answerInput = document.getElementById('user_answer');
    const wordCountEl = document.getElementById('wordCount');
    const timerEl = document.getElementById('timer');
    const voiceBtn = document.getElementById('voiceBtn');
    const submitBtn = document.getElementById('submitBtn');
    const answerForm = document.getElementById('answerForm');

    // 1. Word Counter
    if (answerInput && wordCountEl) {
        const updateWordCount = () => {
            const text = answerInput.value.trim();
            const words = text ? text.split(/\s+/).length : 0;
            wordCountEl.textContent = `${words} words`;
        };
        answerInput.addEventListener('input', updateWordCount);
        updateWordCount();
    }

    // 2. Stopwatch Timer
    if (timerEl) {
        let seconds = 0;
        setInterval(() => {
            seconds++;
            const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
            const secs = (seconds % 60).toString().padStart(2, '0');
            timerEl.textContent = `${mins}:${secs}`;
        }, 1000);
    }

    // 3. Web Speech API Integration (Voice Input)
    if (voiceBtn && answerInput) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = 'en-US';

            let isListening = false;

            voiceBtn.addEventListener('click', () => {
                if (!isListening) {
                    recognition.start();
                    isListening = true;
                    voiceBtn.classList.add('voice-btn-active');
                    voiceBtn.innerHTML = '🎙️ Listening... Click to Stop';
                } else {
                    recognition.stop();
                    isListening = false;
                    voiceBtn.classList.remove('voice-btn-active');
                    voiceBtn.innerHTML = '🎤 Voice Dictation';
                }
            });

            recognition.onresult = (event) => {
                let transcript = '';
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    transcript += event.results[i][0].transcript;
                }
                
                // Append transcript to textarea
                const currentText = answerInput.value;
                if (event.results[0].isFinal) {
                    answerInput.value = currentText ? (currentText + ' ' + transcript.trim()) : transcript.trim();
                    answerInput.dispatchEvent(new Event('input'));
                }
            };

            recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                isListening = false;
                voiceBtn.classList.remove('voice-btn-active');
                voiceBtn.innerHTML = '🎤 Voice Dictation';
            };

            recognition.onend = () => {
                isListening = false;
                voiceBtn.classList.remove('voice-btn-active');
                voiceBtn.innerHTML = '🎤 Voice Dictation';
            };
        } else {
            voiceBtn.style.display = 'none';
            console.log('Web Speech API is not supported in this browser.');
        }
    }

    // 4. Form Submit Loading Spinner
    if (answerForm && submitBtn) {
        answerForm.addEventListener('submit', () => {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '✨ AI Evaluating Answer...';
        });
    }
});
