# Portuguese Gap-Capture

A smart language learning tool that helps you practice Portuguese by recording your speech and identifying when you switch to English for unknown phrases.

## Current Features

1. **Real-time Audio Recording** - Record your Portuguese speech with browser-based audio capture
2. **Language Segment Marking** - Press spacebar to toggle between Portuguese and English modes
3. **Complete Span Tracking** - Tracks all language segments with timestamps
4. **Dual Transcription Approaches** - Compare auto-detect vs segmented-parallel methods
5. **Performance Comparison** - Side-by-side timing and quality analysis
6. **Clean Results Display** - See transcripts from both approaches with detailed metrics

## How It Works

1. **Start Recording** - Click "Start Recording" and begin speaking Portuguese
2. **Mark Language Segments** - Press spacebar to toggle between Portuguese and English modes
   - The interface dramatically changes to blue/purple theme to indicate English mode
3. **Stop Recording** - Click "Stop Recording" when finished
4. **Compare Results** - View transcripts from both approaches side-by-side with performance metrics

## Tech Stack

- **Frontend**: HTML/CSS/JavaScript (Vanilla)
- **Backend**: Python with FastAPI
- **Audio Processing**: librosa for audio segmentation
- **AI Transcription**: OpenAI Whisper API
- **Styling**: Modern CSS with gradient backgrounds and smooth animations

## Next Steps

- **Segmented-Parallel Approach** - Implement parallel transcription of individual segments
- **Performance Comparison** - Compare auto-detect vs segmented approaches
- **Translation Integration** - Add Portuguese translations for English segments
- **Flashcard Generation** - Create practice cards from identified gaps
- **Database Integration** - Store vocabulary and learning progress

## Contributing

This project is in active development. Check [NEXT_STEPS.md](./NEXT_STEPS.md) for current priorities.

## License

MIT License - see LICENSE file for details
