class AudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.isEnglishMode = false;
        this.spans = [];
        this.startTime = 0;
        this.timerInterval = null;
        
        this.initializeElements();
        this.bindEvents();
    }

    initializeElements() {
        this.recordBtn = document.getElementById('recordBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.statusDot = document.getElementById('statusDot');
        this.statusText = document.getElementById('statusText');
        this.timer = document.getElementById('timer');
        this.currentLang = document.getElementById('currentLang');
        this.resultsSection = document.getElementById('resultsSection');
        this.processingStatus = document.getElementById('processingStatus');
    }

    bindEvents() {
        this.recordBtn.addEventListener('click', () => this.startRecording());
        this.stopBtn.addEventListener('click', () => this.stopRecording());
        
        // Spacebar event listener - single press to toggle English mode
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && this.isRecording) {
                e.preventDefault();
                this.toggleEnglishMode();
            }
        });
    }

    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];
            this.spans = [];
            this.startTime = Date.now();
            this.isRecording = true;
            this.isEnglishMode = false;

            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };

            this.mediaRecorder.onstop = () => {
                this.processRecording();
            };

            this.mediaRecorder.start();
            this.updateUI();
            this.startTimer();
            
            console.log('Recording started');
        } catch (error) {
            console.error('Error starting recording:', error);
            alert('Error accessing microphone. Please check permissions.');
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.isEnglishMode = false;
            this.stopTimer();
            this.updateUI();
            
            // Stop all tracks
            this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
            
            console.log('Recording stopped');
        }
    }

    toggleEnglishMode() {
        const currentTime = this.getCurrentTime();
        
        if (!this.isEnglishMode) {
            // Starting English mode
            this.isEnglishMode = true;
            this.spans.push({
                start: currentTime,
                end: null,
                language: 'english'
            });
        } else {
            // Ending English mode
            this.isEnglishMode = false;
            if (this.spans.length > 0) {
                this.spans[this.spans.length - 1].end = currentTime;
            }
        }
        
        this.updateUI();
    }

    getCurrentTime() {
        return (Date.now() - this.startTime) / 1000;
    }

    startTimer() {
        this.timerInterval = setInterval(() => {
            const elapsed = this.getCurrentTime();
            this.timer.textContent = this.formatTime(elapsed);
        }, 100);
    }

    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }

    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    updateUI() {
        // Update buttons
        this.recordBtn.disabled = this.isRecording;
        this.stopBtn.disabled = !this.isRecording;

        // Update status with dramatic visual changes for English mode
        if (this.isRecording) {
            if (this.isEnglishMode) {
                // Dramatic English mode styling
                this.statusDot.className = 'status-dot english-recording';
                this.statusText.textContent = 'RECORDING ENGLISH';
                this.statusText.className = 'status-text english-mode';
                this.currentLang.textContent = 'ENGLISH';
                this.currentLang.className = 'lang-badge english-mode';
                
                // Add English mode visual effects to the entire recording section
                document.querySelector('.recording-section').classList.add('english-mode-active');
                document.querySelector('.timer').classList.add('english-mode');
            } else {
                // Normal Portuguese mode
                this.statusDot.className = 'status-dot recording';
                this.statusText.textContent = 'Recording Portuguese';
                this.statusText.className = 'status-text';
                this.currentLang.textContent = 'Portuguese';
                this.currentLang.className = 'lang-badge';
                
                // Remove English mode effects
                document.querySelector('.recording-section').classList.remove('english-mode-active');
                document.querySelector('.timer').classList.remove('english-mode');
            }
        } else {
            // Not recording
            this.statusDot.className = 'status-dot';
            this.statusText.textContent = 'Ready to record';
            this.statusText.className = 'status-text';
            this.currentLang.textContent = 'Portuguese';
            this.currentLang.className = 'lang-badge';
            
            // Remove English mode effects
            document.querySelector('.recording-section').classList.remove('english-mode-active');
            document.querySelector('.timer').classList.remove('english-mode');
        }
    }

    async processRecording() {
        this.resultsSection.style.display = 'block';
        this.processingStatus.textContent = 'Processing your recording...';

        // Create audio blob
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
        
        // Prepare data for backend
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');
        formData.append('spans', JSON.stringify(this.spans));
        formData.append('duration', this.getCurrentTime().toString());

        try {
            // Send to backend API
            const response = await fetch('/process-recording', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            // Display the transcription results
            this.displayTranscriptionResults(result);
            console.log('Backend response:', result);
            
        } catch (error) {
            console.error('Error processing recording:', error);
            this.processingStatus.textContent = 'Error processing recording. Please try again.';
        }
    }

    displayTranscriptionResults(result) {
        let resultsHTML = '';
        
        // Check for error response
        if (result.error) {
            resultsHTML += `<div class="error-section">
                <h4>❌ Error</h4>
                <p>${result.error}</p>
            </div>`;
            this.processingStatus.innerHTML = resultsHTML;
            return;
        }
        
        // Display complete transcript with highlighted English segments
        if (result.full_transcript) {
            let highlightedTranscript = result.full_transcript;
            
            // Highlight English segments if we have transcription data
            if (result.transcriptions && result.transcriptions.length > 0) {
                // Find English segments and highlight them with translations
                result.transcriptions.forEach((segment) => {
                    if (segment.language === 'english' && segment.text) {
                        // Escape special regex characters in the text
                        const escapedText = segment.text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                        const regex = new RegExp(escapedText, 'g');
                        
                        // Create hover tooltip with translation
                        const translation = segment.translation || 'Translation not available';
                        const tooltipText = `English: ${segment.text}<br>Portuguese: ${translation}`;
                        
                        highlightedTranscript = highlightedTranscript.replace(
                            regex,
                            `<span class="english-highlight" title="${tooltipText}">${segment.text}</span>`
                        );
                    }
                });
            }
            
            resultsHTML += `
                <div class="transcript-container">
                    <h3>Complete Transcript</h3>
                    <div class="transcript-text">${highlightedTranscript}</div>
                </div>
            `;
        }
        
        // Display translations list
        if (result.transcriptions && result.transcriptions.length > 0) {
            const englishSegments = result.transcriptions.filter(segment => segment.language === 'english');
            
            console.log('English segments found:', englishSegments);
            
            if (englishSegments.length > 0) {
                resultsHTML += `
                    <div class="translations-container">
                        <h3>🔤 English Phrases & Translations</h3>
                        <div class="translations-list">
                `;
                
                englishSegments.forEach((segment, index) => {
                    const translation = segment.translation || 'Translation not available';
                    console.log(`Translation ${index}: "${segment.text}" → "${translation}"`);
                    resultsHTML += `
                        <div class="translation-item">
                            <div class="translation-english">
                                <strong>English:</strong> ${segment.text}
                            </div>
                            <div class="translation-arrow">→</div>
                            <div class="translation-portuguese">
                                <strong>Portuguese:</strong> ${translation}
                            </div>
                        </div>
                    `;
                });
                
                resultsHTML += `
                        </div>
                    </div>
                `;
            } else {
                resultsHTML += `
                    <div class="translations-container">
                        <h3>🔤 English Phrases & Translations</h3>
                        <p style="text-align: center; color: #666; font-style: italic;">
                            No English segments detected in this recording.
                        </p>
                    </div>
                `;
            }
        } else {
            resultsHTML += `
                <div class="translations-container">
                    <h3>🔤 English Phrases & Translations</h3>
                    <p style="text-align: center; color: #666; font-style: italic;">
                        No transcription data available.
                    </p>
                </div>
            `;
        }
        
        this.processingStatus.innerHTML = resultsHTML;
    }
}

// Initialize the recorder when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new AudioRecorder();
});
