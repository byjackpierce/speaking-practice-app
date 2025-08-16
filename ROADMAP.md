# Technical Roadmap

## Learning Approach

This project is designed as a **hands-on learning experience**. You'll write all the code yourself while working through each phase step-by-step. The goal is to understand the concepts, make mistakes, and learn from the process rather than just copying code.

## MVP Build Order

### Phase 1: Core Recording System
- [ ] Frontend recording interface with spacebar span capture
- [ ] Backend endpoint for audio + span metadata storage
- [ ] Visual indicators for "English mode" activation

### Phase 2: Speech Processing
- [ ] Whisper large-v3 ASR integration
- [ ] Language detection with spacebar span override
- [ ] Token-level language ID fallback
- [ ] English segment extraction

### Phase 3: Translation Engine
- [ ] GPT-4 integration for Portuguese translation
- [ ] Colloquial variant generation (2-3 per phrase)
- [ ] False friend detection and notes
- [ ] Deduplication and frequency ranking

### Phase 4: Dialogue Generation
- [ ] LLM-powered 2-person conversation creation
- [ ] Target phrase integration (2-3x each)
- [ ] Unknown vocabulary capping (≤10%)
- [ ] Topic relevance to original monologue

### Phase 5: Audio Output
- [ ] Brazilian TTS integration
- [ ] Full dialogue and per-line audio generation
- [ ] Playback speed controls (0.9x, 1.0x, 1.1x)
- [ ] Natural prosody and contractions

### Phase 6: Export & Tracking
- [ ] Anki CSV export (Portuguese front, English hint, example, audio)
- [ ] LingQ export option
- [ ] SQLite database setup
- [ ] Progress tracking (gap closure, reuse count)

## Database Schema

```sql
-- Target phrases
targets: id, en_text, pt_default, pt_variants[], notes, first_seen, exposures, status

-- Recording sessions  
sessions: id, audio_id, spans[{t0, t1, lang}], chosen_targets[]

-- Known vocabulary
known_vocab: word, first_seen, last_reviewed, confidence
```

## Quality Gates

- **Dialogue Rejection Criteria:**
  - Targets used <2x each
  - Unknown vocab ratio >10%
  - Non-colloquial register
- **TTS Preferences:**
  - Sentence-level prosody
  - Contractions ("tá" over "está")
  - Brazilian accent and intonation

## Tech Stack Details

- **Frontend**: Vanilla JS, Web Audio API, MediaRecorder
- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **AI Services**: OpenAI API (GPT-4), Whisper API
- **TTS**: ElevenLabs or Azure Speech Services
- **Database**: SQLite with Alembic migrations

## Learning-Focused Next Steps

1. **Set up project structure and dependencies** - Learn about project organization and dependency management
2. **Implement basic recording interface** - Understand Web Audio API and event handling
3. **Integrate Whisper ASR** - Learn about API integration and async programming
4. **Build translation pipeline** - Explore prompt engineering and AI service integration

## Development Philosophy

- **Write everything yourself** - No copy-pasting, understand each line
- **Make mistakes** - Learn from errors and debugging
- **Ask questions** - Discuss concepts before implementation
- **Go slow** - Take time to understand before moving forward
- **Iterate** - Refactor and improve as you learn
