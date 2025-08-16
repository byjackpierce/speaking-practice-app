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
        this.spansList = document.getElementById('spansList');
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
        this.updateSpansDisplay();
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

        // Update status
        if (this.isRecording) {
            this.statusDot.className = 'status-dot recording';
            this.statusText.textContent = this.isEnglishMode ? 'Recording (English Mode)' : 'Recording (Portuguese)';
        } else {
            this.statusDot.className = 'status-dot';
            this.statusText.textContent = 'Ready to record';
        }

        // Update language indicator
        this.currentLang.textContent = this.isEnglishMode ? 'English' : 'Portuguese';
        this.currentLang.className = `lang-badge ${this.isEnglishMode ? 'english' : ''}`;
    }

    updateSpansDisplay() {
        if (this.spans.length === 0) {
            this.spansList.innerHTML = '<p class="empty-state">Press spacebar to mark English segments</p>';
            return;
        }

        this.spansList.innerHTML = '';
        
        this.spans.forEach((span, index) => {
            const spanElement = document.createElement('div');
            spanElement.className = 'span-item';
            
            const startTime = this.formatTime(span.start);
            const endTime = span.end ? this.formatTime(span.end) : '...';
            const duration = span.end ? this.formatTime(span.end - span.start) : '';
            
            spanElement.innerHTML = `
                <div>
                    <div class="span-time">${startTime} - ${endTime}</div>
                    <div class="span-duration">${duration}</div>
                </div>
            `;
            
            this.spansList.appendChild(spanElement);
        });
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
        let resultsHTML = '<h3>Transcription Results</h3>';
        
        if (result.transcription) {
            // Simple case - full transcription
            resultsHTML += `
                <div class="transcription-result">
                    <h4>Full Transcript:</h4>
                    <p class="transcript-text">${result.transcription}</p>
                </div>
            `;
        } else if (result.transcriptions && result.transcriptions.length > 0) {
            // Segmented transcription
            resultsHTML += '<div class="transcription-segments">';
            result.transcriptions.forEach((segment, index) => {
                resultsHTML += `
                    <div class="transcription-segment">
                        <div class="segment-header">
                            <span class="segment-time">${this.formatTime(segment.start_time)} - ${this.formatTime(segment.end_time)}</span>
                            <span class="segment-language">${segment.language}</span>
                        </div>
                        <p class="segment-text">${segment.text}</p>
                    </div>
                `;
            });
            resultsHTML += '</div>';
        }
        
        if (result.full_transcript) {
            resultsHTML += `
                <div class="full-transcript">
                    <h4>Combined Transcript:</h4>
                    <p class="transcript-text">${result.full_transcript}</p>
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
