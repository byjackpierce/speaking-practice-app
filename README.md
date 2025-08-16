# Portuguese Gap-Capture

A smart language learning tool that helps you practice Portuguese by recording your speech and identifying when you switch to English for unknown phrases.

## Current Features (MVP)

1. **Real-time Audio Recording** - Record your Portuguese speech with browser-based audio capture
2. **Language Segment Marking** - Press spacebar to mark when you switch to English
3. **Intelligent Audio Splitting** - Automatically separates Portuguese and English segments
4. **Whisper Transcription** - AI-powered transcription for both languages
5. **Beautiful Results Display** - See your transcribed segments with timing and language labels

## How It Works

1. **Start Recording** - Click "Start Recording" and begin speaking Portuguese
2. **Mark English Segments** - Press spacebar when you need to switch to English for unknown words/phrases
3. **Stop Recording** - Click "Stop Recording" when finished
4. **View Results** - See your transcribed speech with Portuguese and English segments clearly marked

## Tech Stack

- **Frontend**: HTML/CSS/JavaScript (Vanilla)
- **Backend**: Python with FastAPI
- **Audio Processing**: librosa for audio segmentation
- **AI Transcription**: OpenAI Whisper API
- **Styling**: Modern CSS with gradient backgrounds and smooth animations

## Getting Started

### Prerequisites
- Python 3.8+
- OpenAI API key
- ffmpeg (for audio processing)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd speaking-practice-app
   ```

2. **Install backend dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the backend directory:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

4. **Install ffmpeg** (required for audio processing)
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt install ffmpeg
   ```

5. **Start the server**
   ```bash
   cd backend
   python3 -m uvicorn main:app --reload
   ```

6. **Open your browser**
   Navigate to `http://localhost:8000`

## Usage

1. Allow microphone access when prompted
2. Click "Start Recording" and begin speaking Portuguese
3. Press spacebar whenever you switch to English for unknown words
4. Click "Stop Recording" when finished
5. View your transcribed results with language segments clearly marked

## Future Features

- Translation of English segments to Portuguese
- Practice dialogue generation
- Progress tracking
- Anki integration
- Audio playback with TTS

## Contributing

This project is in active development. Check the [Technical Roadmap](./ROADMAP.md) for current priorities and contribution opportunities.

## License

MIT License - see LICENSE file for details
