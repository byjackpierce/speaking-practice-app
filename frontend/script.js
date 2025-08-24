class AudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.spans = [];
        this.startTime = null;
        this.isRecording = false;
        this.isEnglishMode = false;

        // DOM elements
        this.recordBtn = document.getElementById('recordBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.statusDot = document.getElementById('statusDot');
        this.statusText = document.getElementById('statusText');
        this.timer = document.getElementById('timer');
        this.currentLang = document.getElementById('currentLang');
        this.resultsSection = document.getElementById('resultsSection');
        this.processingStatus = document.getElementById('processingStatus');

        // Event listeners
        this.recordBtn.addEventListener('click', () => this.startRecording());
        this.stopBtn.addEventListener('click', () => this.stopRecording());
        document.addEventListener('keydown', (e) => this.handleKeyPress(e));
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

            // Start with Portuguese span
            this.spans.push({
                start: 0,
                end: null,
                language: 'portuguese'
            });

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
        if (!this.isRecording) return;

        this.isRecording = false;
        this.mediaRecorder.stop();
        
        // Finalize the last span
        const finalTime = this.getCurrentTime();
        if (this.spans.length > 0) {
            this.spans[this.spans.length - 1].end = finalTime;
        }
        
        console.log('Final spans:', this.spans);
        console.log('Coverage:', this.spans.reduce((total, span) => total + (span.end - span.start), 0), 'seconds');
        
        this.updateUI();
        this.stopTimer();
        
        // Enable test button after recording
        // this.testVerboseBtn.disabled = false; // Removed test button
    }

    handleKeyPress(event) {
        if (event.code === 'Space' && this.isRecording) {
            event.preventDefault();
            this.toggleEnglishMode();
        }
    }

    toggleEnglishMode() {
        const currentTime = this.getCurrentTime();
        
        if (!this.isEnglishMode) {
            // Starting English mode
            this.isEnglishMode = true;
            
            // End the current Portuguese span
            if (this.spans.length > 0) {
                this.spans[this.spans.length - 1].end = currentTime;
            }
            
            // Start new English span
            this.spans.push({
                start: currentTime,
                end: null,
                language: 'english'
            });
        } else {
            // Ending English mode
            this.isEnglishMode = false;
            
            // End the current English span
            if (this.spans.length > 0) {
                this.spans[this.spans.length - 1].end = currentTime;
            }
            
            // Start new Portuguese span
            this.spans.push({
                start: currentTime,
                end: null,
                language: 'portuguese'
            });
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
                throw new Error(`API error! status: ${response.status}`);
            }

            const result = await response.json();
            
            // Display results
            this.displayResult(result);
            console.log('Transcription response:', result);
            
        } catch (error) {
            console.error('Error processing recording:', error);
            this.processingStatus.textContent = 'Error processing recording. Please try again.';
        }
    }

    displayResult(result) {
        let resultsHTML = '';
        
        // Check for errors
        if (result.error) {
            resultsHTML = `<div class="error-section">
                <h4>❌ Error</h4>
                <p>${result.error}</p>
            </div>`;
            this.processingStatus.innerHTML = resultsHTML;
            return;
        }
        
        // Display transcript
        resultsHTML = `
            <div class="result-header">
                <h2>📝 Your Transcript</h2>
            </div>
            
            <div class="transcript-section">
                <div class="transcript-text">${result.transcript}</div>
            </div>
            
            <div class="info-section">
                <div class="info-item">
                    <span class="info-label">Duration:</span>
                    <span class="info-value">${result.duration.toFixed(1)}s</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Processing time:</span>
                    <span class="info-value">${result.total_time.toFixed(2)}s</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Segments:</span>
                    <span class="info-value">${result.segments_count}</span>
                </div>
            </div>
        `;
        
        this.processingStatus.innerHTML = resultsHTML;
    }
}

// Initialize the recorder when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new AudioRecorder();
});
