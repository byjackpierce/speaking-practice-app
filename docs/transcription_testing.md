# Transcription Approach Testing

## Current State

### Auto-Detect Approach (Working)
- **Status**: ✅ Implemented and working
- **Method**: Uses Whisper API with language detection prompt
- **Input**: Complete spans data (Portuguese and English segments)
- **Output**: Single transcript with mixed language detection

### Next Phase: Segmented-Parallel Approach (To Implement)
- **Method**: Split by spans, transcribe ALL segments simultaneously
- **Goal**: Compare performance and quality with auto-detect approach

### Implementation Plan:
- Add segmented-parallel endpoint
- Real-time performance comparison
- User voting system for quality assessment
- Results stored in JSON file
- **No translation** - focus purely on transcription quality

### Success Metrics:
- Processing speed (seconds)
- Transcription accuracy (user votes)
- Grammar quality (user assessment)

### Expected Outcome:
Identify optimal transcription approach for mixed Portuguese-English language learning.

---

# Detailed Implementation Plan

## Phase 1: Auto-Detect-Prompt Approach (Simpler - Start Here)

### File: `backend/main.py`
**Add new endpoint:**
```python
@app.post("/process-recording-auto-detect")
```

### Input Data:
- `audio: UploadFile` - Audio file from frontend
  ```
  {
    "filename": "recording.wav",
    "content_type": "audio/wav",
    "file": <binary audio data>
  }
  ```

- `spans: str` - JSON string of language spans (Portuguese and English with timestamps)
  ```json
[
  {
    "start": 0.0,
    "end": 5.2,
    "language": "portuguese"
  },
  {
    "start": 5.2,
    "end": 8.1, 
    "language": "english"
  },
  {
    "start": 8.1,
    "end": 12.5,
    "language": "portuguese"
  },
  {
    "start": 12.5,
    "end": 15.8,
    "language": "english"
  },
  {
    "start": 15.8,
    "end": 30.0,
    "language": "portuguese"
  }
]
  ```

- `duration: str` - Recording duration in seconds
  ```
  "8.1"
  ```

### Processing Flow:
1. **Load audio** → Save to temporary file
2. **Start timing** → Record start time
3. **Transcribe** → Call Whisper API with prompt
4. **End timing** → Calculate total time
5. **Format response** → Create performance metrics
6. **Clean up** → Delete temporary file

### Whisper API Call:
```python
transcript = client.audio.transcriptions.create(
    model="whisper-1",
    file=audio_file,
    prompt="Language learning: Portuguese speaker mixing Portuguese and English. Transcribe each language as spoken. No translation."
)
```

### Output Structure:
```json
{
  "message": "success",
  "duration": 30.5,
  "transcript": "Agora eu falo português e agora practice English...",
  "performance_metrics": {
    "total_time": 2.1,
    "transcription_time": 2.1,
    "approach": "auto_detect_prompt"
  }
}
```

### Timing Points to Track:
- `start_time` - When function begins
- `transcription_start` - When Whisper API call starts
- `transcription_end` - When Whisper API call ends
- `total_time` = transcription_end - start_time

---

## Phase 2: Segmented-Parallel Approach (More Complex)

### File: `backend/main.py`
**Add new endpoint:**
```python
@app.post("/process-recording-segmented-parallel")
```

### Input Data:
- `audio: UploadFile` - Audio file from frontend
- `spans: str` - JSON string of language spans
- `duration: str` - Recording duration in seconds

### Processing Flow:
1. **Load audio** → Save to temporary file
2. **Start timing** → Record start time
3. **Create segments** → Split audio by spans (use existing `split_audio_by_spans`)
4. **Segment timing** → Record segmentation time
5. **Transcribe segments** → Call Whisper API for ALL segments simultaneously (parallel)
6. **Combine results** → Merge all transcripts
7. **End timing** → Calculate total time
8. **Format response** → Create performance metrics
9. **Clean up** → Delete temporary files

### Parallel Processing:
```python
# Create tasks for all segments
tasks = []
for segment in segments:
    task = transcribe_segment_parallel(segment, client)
    tasks.append(task)

# Run all transcriptions simultaneously
results = await asyncio.gather(*tasks)
```

### Output Structure:
```json
{
  "message": "success",
  "duration": 30.5,
  "transcript": "Agora eu falo português e agora practice English...",
  "performance_metrics": {
    "total_time": 1.8,
    "segmentation_time": 0.3,
    "transcription_time": 1.5,
    "segments_count": 3,
    "approach": "segmented_parallel"
  }
}
```

### Timing Points to Track:
- `start_time` - When function begins
- `segmentation_start` - When audio splitting begins
- `segmentation_end` - When audio splitting ends
- `transcription_start` - When parallel transcription begins
- `transcription_end` - When parallel transcription ends
- `total_time` = transcription_end - start_time

---

## Phase 3: Comparison Endpoint

### File: `backend/main.py`
**Add new endpoint:**
```python
@app.post("/process-recording-comparison")
```

### Processing Flow:
1. **Receive input** → Audio file, spans, duration
2. **Run both approaches** → Call both endpoints in parallel
3. **Collect results** → Get results from both approaches
4. **Format comparison** → Create side-by-side comparison
5. **Return results** → Send both results to frontend

### Output Structure:
```json
{
  "message": "success",
  "duration": 30.5,
  "results": {
    "segmented_parallel": {
      "transcript": "...",
      "performance": {...}
    },
    "auto_detect_prompt": {
      "transcript": "...",
      "performance": {...}
    }
  }
}
```

---

## Phase 4: Frontend Updates

### File: `frontend/script.js`
**Update `processRecording()` function:**
1. **Change API call** → Call `/process-recording-comparison`
2. **Update display** → Show 2-column comparison
3. **Add voting** → Add vote buttons for each approach
4. **Store results** → Save user vote to JSON file

### New UI Elements:
- **2-column layout** → Side-by-side results
- **Vote buttons** → �� for each approach
- **Performance metrics** → Show timing for each
- **Transcript display** → Show both transcripts

---

## Phase 5: Results Storage

### File: `data/experiment_results.json`
**Structure for storing results:**
```json
{
  "experiments": [
    {
      "experiment_id": "2024-01-15-001",
      "timestamp": "2024-01-15T10:30:00Z",
      "input": {
        "duration": 30.5,
        "spans_count": 2
      },
      "results": {
        "segmented_parallel": {
          "transcript": "...",
          "performance": {...}
        },
        "auto_detect_prompt": {
          "transcript": "...",
          "performance": {...}
        }
      },
      "user_vote": "segmented_parallel",
      "vote_timestamp": "2024-01-15T10:32:00Z"
    }
  ]
}
```

---

## Implementation Order:

1. **Phase 1** → Auto-detect endpoint (simpler)
2. **Phase 2** → Segmented-parallel endpoint (more complex)
3. **Phase 3** → Comparison endpoint (combines both)
4. **Phase 4** → Frontend updates (UI changes)
5. **Phase 5** → Results storage (data persistence)

---

## Testing Strategy:

1. **Test Phase 1** → Verify auto-detect works
2. **Test Phase 2** → Verify segmented-parallel works
3. **Test Phase 3** → Verify comparison works
4. **Test Phase 4** → Verify frontend displays correctly
5. **Test Phase 5** → Verify results are stored

---

## Success Criteria:

- Both approaches complete successfully
- Performance metrics are accurate
- Frontend displays comparison clearly
- User can vote on preferred approach
- Results are stored in JSON file
- No errors in processing or display