# Portuguese Gap-Capture

A smart language learning tool that helps you practice Portuguese by recording your speech and identifying when you switch to English for unknown phrases.

## Current Features

1. **Real-time Audio Recording** - Record your Portuguese speech with browser-based audio capture
2. **Language Segment Marking** - Press spacebar to mark when you switch to English (with dramatic visual feedback)
3. **Intelligent Audio Splitting** - Automatically separates Portuguese and English segments
4. **Whisper Transcription** - AI-powered transcription for both languages
5. **Clean Results Display** - See your complete transcript with English segments highlighted

## How It Works

1. **Start Recording** - Click "Start Recording" and begin speaking Portuguese
2. **Mark English Segments** - Press spacebar when you need to switch to English for unknown words/phrases
   - The interface dramatically changes to blue/purple theme to indicate English mode
3. **Stop Recording** - Click "Stop Recording" when finished
4. **View Results** - See your complete transcript with English segments subtly highlighted

## Tech Stack

- **Frontend**: HTML/CSS/JavaScript (Vanilla)
- **Backend**: Python with FastAPI
- **Audio Processing**: librosa for audio segmentation
- **AI Transcription**: OpenAI Whisper API
- **Styling**: Modern CSS with gradient backgrounds and smooth animations

## Next Steps

- Translation of English segments to Portuguese
- Flashcard generation for practice
- Content generation for continued learning
- Database for vocabulary tracking

## Contributing

This project is in active development. Check [NEXT_STEPS.md](./NEXT_STEPS.md) for current priorities.

## License

MIT License - see LICENSE file for details
