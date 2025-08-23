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
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.isEnglishMode = false;
            this.stopTimer();
            
            // Finalize the last span
            const finalTime = this.getCurrentTime();
            if (this.spans.length > 0) {
                this.spans[this.spans.length - 1].end = finalTime;
            }
            
            this.updateUI();
            
            // Stop all tracks
            this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
            
            console.log('Recording stopped');
            console.log('Final spans:', this.spans);
            
            // Validate spans coverage
            const totalDuration = this.getCurrentTime();
            let totalCovered = 0;
            this.spans.forEach((span, index) => {
                const spanDuration = span.end - span.start;
                totalCovered += spanDuration;
                console.log(`Span ${index}: ${span.language} from ${span.start.toFixed(2)}s to ${span.end.toFixed(2)}s (${spanDuration.toFixed(2)}s)`);
            });
            console.log(`Total duration: ${totalDuration.toFixed(2)}s, Total covered: ${totalCovered.toFixed(2)}s`);
            console.log(`Coverage: ${((totalCovered / totalDuration) * 100).toFixed(1)}%`);
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
            const [autoDetectResponse, segmentedResponse] = await Promise.all([
                fetch('/process-recording-auto-detect', {
                    method: 'POST',
                    body: formData
                }),
                fetch('/process-recording-segmented-parallel', {
                    method: 'POST',
                    body: formData
                })
            ]);

            if (!autoDetectResponse.ok) {
                throw new Error(`Auto-detect API error! status: ${autoDetectResponse.status}`);
            }
            if (!segmentedResponse.ok) {
                throw new Error(`Segmented-parallel API error! status: ${segmentedResponse.status}`);
            }

            const autoDetectResult = await autoDetectResponse.json();
            const segmentedResult = await segmentedResponse.json();
            
            // Display comparison results
            this.displayComparisonResults(autoDetectResult, segmentedResult);
            console.log('Auto-detect response:', autoDetectResult);
            console.log('Segmented-parallel response:', segmentedResult);
            
        } catch (error) {
            console.error('Error processing recording:', error);
            this.processingStatus.textContent = 'Error processing recording. Please try again.';
        }
    }

    displayComparisonResults(autoDetectResult, segmentedResult) {
        let resultsHTML = '';
        
        // Check for errors
        if (autoDetectResult.error || segmentedResult.error) {
            resultsHTML += `<div class="error-section">
                <h4>❌ Error</h4>
                <p>Auto-detect: ${autoDetectResult.error || 'Success'}</p>
                <p>Segmented-parallel: ${segmentedResult.error || 'Success'}</p>
            </div>`;
            this.processingStatus.innerHTML = resultsHTML;
            return;
        }
        
        // Performance comparison
        const autoDetectTime = autoDetectResult.Total_time || 0;
        const segmentedTime = segmentedResult.Total_time || 0;
        const timeDifference = autoDetectTime - segmentedTime;
        const fasterApproach = timeDifference > 0 ? 'Segmented-Parallel' : 'Auto-Detect';
        
        resultsHTML += `
            <div class="comparison-header">
                <h2>🔄 Transcription Comparison</h2>
                <div class="performance-summary">
                    <div class="performance-item">
                        <span class="approach-label">Auto-Detect:</span>
                        <span class="time-value">${autoDetectTime.toFixed(2)}s</span>
                    </div>
                    <div class="performance-item">
                        <span class="approach-label">Segmented-Parallel:</span>
                        <span class="time-value">${segmentedTime.toFixed(2)}s</span>
                    </div>
                    <div class="performance-item ${timeDifference > 0 ? 'faster' : 'slower'}">
                        <span class="approach-label">🏆 Fastest:</span>
                        <span class="time-value">${fasterApproach} (${Math.min(autoDetectTime, segmentedTime).toFixed(2)}s)</span>
                    </div>
                </div>
            </div>
        `;
        
        // Auto-detect Approach Results
        resultsHTML += `
            <div class="approach-section auto-detect">
                <h3>🤖 Auto-Detect Approach</h3>
                <p class="approach-description">Uses Whisper with language detection prompt to automatically identify Portuguese and English</p>
        `;
        
        if (autoDetectResult.Transcript) {
            resultsHTML += `
                <div class="transcript-container">
                    <h4>Complete Transcript</h4>
                    <div class="transcript-text">${autoDetectResult.Transcript}</div>
                </div>
            `;
        }
        
        resultsHTML += `</div>`;
        
        // Segmented-Parallel Approach Results
        resultsHTML += `
            <div class="approach-section segmented">
                <h3>🎯 Segmented-Parallel Approach</h3>
                <p class="approach-description">Splits audio into segments and transcribes each with language-specific prompts in parallel</p>
        `;
        
        if (segmentedResult.Transcript) {
            resultsHTML += `
                <div class="transcript-container">
                    <h4>Complete Transcript</h4>
                    <div class="transcript-text">${segmentedResult.Transcript}</div>
                </div>
            `;
            
            // Add detailed timing info if available
            if (segmentedResult.Segmentation_time || segmentedResult.Transcription_time) {
                resultsHTML += `
                    <div class="timing-details">
                        <h4>⏱️ Timing Breakdown</h4>
                        <div class="timing-item">
                            <span>Segmentation:</span>
                            <span>${(segmentedResult.Segmentation_time || 0).toFixed(2)}s</span>
                        </div>
                        <div class="timing-item">
                            <span>Transcription:</span>
                            <span>${(segmentedResult.Transcription_time || 0).toFixed(2)}s</span>
                        </div>
                        <div class="timing-item">
                            <span>Segments Processed:</span>
                            <span>${segmentedResult.Segments_count || 0}</span>
                        </div>
                    </div>
                `;
            }
        }
        
        resultsHTML += `</div>`;
        
        this.processingStatus.innerHTML = resultsHTML;
    }
}

// Initialize the recorder when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new AudioRecorder();
});
