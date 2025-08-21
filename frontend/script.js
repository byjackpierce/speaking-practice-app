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
        this.processingStatus.textContent = 'Processing your recording with both approaches...';

        // Create audio blob
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
        
        // Prepare data for backend
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');
        formData.append('spans', JSON.stringify(this.spans));
        formData.append('duration', this.getCurrentTime().toString());

        try {
            // Send to both backend APIs in parallel
            const [segmentedResponse, simpleResponse] = await Promise.all([
                fetch('/process-recording', {
                    method: 'POST',
                    body: formData
                }),
                fetch('/process-recording-simple', {
                    method: 'POST',
                    body: formData
                })
            ]);

            if (!segmentedResponse.ok) {
                throw new Error(`Segmented API error! status: ${segmentedResponse.status}`);
            }
            if (!simpleResponse.ok) {
                throw new Error(`Simple API error! status: ${simpleResponse.status}`);
            }

            const segmentedResult = await segmentedResponse.json();
            const simpleResult = await simpleResponse.json();
            
            // Display both results
            this.displayComparisonResults(segmentedResult, simpleResult);
            console.log('Segmented response:', segmentedResult);
            console.log('Simple response:', simpleResult);
            
        } catch (error) {
            console.error('Error processing recording:', error);
            this.processingStatus.textContent = 'Error processing recording. Please try again.';
        }
    }

    displayComparisonResults(segmentedResult, simpleResult) {
        let resultsHTML = '';
        
        // Check for errors
        if (segmentedResult.error || simpleResult.error) {
            resultsHTML += `<div class="error-section">
                <h4>❌ Error</h4>
                <p>Segmented: ${segmentedResult.error || 'Success'}</p>
                <p>Simple: ${simpleResult.error || 'Success'}</p>
            </div>`;
            this.processingStatus.innerHTML = resultsHTML;
            return;
        }
        
        // Performance comparison
        const segmentedTime = segmentedResult.performance_metrics?.timing?.total_time || 0;
        const simpleTime = simpleResult.performance_metrics?.timing?.total_time || 0;
        const timeDifference = segmentedTime - simpleTime;
        const fasterApproach = timeDifference > 0 ? 'Simple' : 'Segmented';
        
        resultsHTML += `
            <div class="comparison-header">
                <h2>🔄 Transcription Comparison</h2>
                <div class="performance-summary">
                    <div class="performance-item">
                        <span class="approach-label">Segmented:</span>
                        <span class="time-value">${segmentedTime.toFixed(2)}s</span>
                    </div>
                    <div class="performance-item">
                        <span class="approach-label">Simple:</span>
                        <span class="time-value">${simpleTime.toFixed(2)}s</span>
                    </div>
                    <div class="performance-item ${timeDifference > 0 ? 'faster' : 'slower'}">
                        <span class="approach-label">Difference:</span>
                        <span class="time-value">${Math.abs(timeDifference).toFixed(2)}s ${fasterApproach} is faster</span>
                    </div>
                </div>
            </div>
        `;
        
        // Segmented Approach Results
        resultsHTML += `
            <div class="approach-section segmented">
                <h3>🎯 Segmented Approach</h3>
                <p class="approach-description">Processes each segment separately with language detection</p>
        `;
        
        if (segmentedResult.full_transcript) {
            let highlightedTranscript = segmentedResult.full_transcript;
            
            if (segmentedResult.transcriptions && segmentedResult.transcriptions.length > 0) {
                segmentedResult.transcriptions.forEach((segment) => {
                    if (segment.language === 'english' && segment.text) {
                        const escapedText = segment.text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                        const regex = new RegExp(escapedText, 'g');
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
                    <h4>Complete Transcript</h4>
                    <div class="transcript-text">${highlightedTranscript}</div>
                </div>
            `;
        }
        
        // Segmented translations
        if (segmentedResult.transcriptions && segmentedResult.transcriptions.length > 0) {
            const englishSegments = segmentedResult.transcriptions.filter(segment => segment.language === 'english');
            if (englishSegments.length > 0) {
                resultsHTML += `
                    <div class="translations-container">
                        <h4>🔤 English Phrases & Translations</h4>
                        <div class="translations-list">
                `;
                
                englishSegments.forEach((segment) => {
                    const translation = segment.translation || 'Translation not available';
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
            }
        }
        
        resultsHTML += `</div>`;
        
        // Simple Approach Results
        resultsHTML += `
            <div class="approach-section simple">
                <h3>⚡ Simple Approach</h3>
                <p class="approach-description">Processes entire audio as Portuguese for better grammar flow</p>
        `;
        
        if (simpleResult.full_transcript) {
            resultsHTML += `
                <div class="transcript-container">
                    <h4>Complete Transcript</h4>
                    <div class="transcript-text">${simpleResult.full_transcript}</div>
                </div>
            `;
        }
        
        resultsHTML += `</div>`;
        
        this.processingStatus.innerHTML = resultsHTML;
    }
}

// Initialize the recorder when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new AudioRecorder();
});
