from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import os
import tempfile
import time
from openai import OpenAI
import asyncio
import soundfile
import librosa

"""
Portuguese Gap-Capture API
==========================

FastAPI application for processing mixed Portuguese-English audio recordings.
Uses segmented-parallel transcription approach for optimal language detection.

Endpoints:
- POST /process-recording: Segmented-parallel transcription
- GET /: Frontend interface
- GET /api/health: Health check
"""

# Import our modular components
from config.settings import settings
from config.logging import logger
from middleware.cors import setup_cors

# Create FastAPI app
app = FastAPI(title=settings.APP_TITLE, version=settings.APP_VERSION)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory=settings.STATIC_FILES_DIR), name="static")

# Setup CORS middleware
setup_cors(app)

@app.get("/")
async def root():
    return FileResponse("../frontend/index.html")

@app.get("/api/health")
async def health():
    return {"message": "Portuguese gap-capture backend"}
    

def save_transcript(results: dict):
    """Save transcript to JSON file."""
    from datetime import datetime
    import logging
    
    file_path = "data/transcripts.json"
    
    try:
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        # Load existing transcripts or create new list
        try:
            with open(file_path, "r") as file:
                all_results = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            all_results = []
        
        # Add new transcript
        new_transcript = {
            "timestamp": datetime.now().isoformat(),
            "duration": results["duration"],
            "transcript": results["transcript"],
            "raw_transcript": results.get("raw_transcript", ""), 
            "spans_count": results["spans_count"],
            "segments_count": results["segments_count"],
            "total_time": results["total_time"],
            "parsing_time": results["parsing_time"],
            "file_setup_time": results["file_setup_time"],
            "audio_loading_time": results["audio_loading_time"],
            "segmentation_time": results["segmentation_time"],
            "transcription_time": results["transcription_time"],
            "grammar_correction_time": results.get("grammar_correction_time", 0),
            "segment_timings": results["segment_timings"]
        }
        
        all_results.append(new_transcript)
        
        # Save back to file
        with open(file_path, "w") as file:
            json.dump(all_results, file, indent=2)
            
        logger.info(f"Saved transcript {len(all_results)} to {file_path}")
        
    except Exception as e:
        logger.error(f"Failed to save transcript: {str(e)}")
        # Don't crash the main function if saving fails
        pass


def create_segments_from_spans(audio_data, spans_data, sample_rate):
    """Create audio segments from spans data."""
    segments = []
    for i, span in enumerate(spans_data):
        # Convert time to sample indices (must be integers)
        start_sample = int(span['start'] * sample_rate)
        end_sample = int(span['end'] * sample_rate)

        # Extract segment audio
        segment_audio = audio_data[start_sample:end_sample]

        # Create segment object
        segments.append({
            'index': i,
            'start_time': span['start'],
            'end_time': span['end'],
            'language': span['language'],
            'audio_data': segment_audio,
            'sample_rate': sample_rate
        })

    return segments

def apply_grammar_correction(transcript: str) -> str:
    """
    Apply grammar correction to mixed Portuguese-English transcript.
    
    Args:
        transcript: Raw transcript with mixed languages
        
    Returns:
        Grammar-corrected transcript with natural flow
    """
    client = OpenAI()
    
    prompt = f"""
You are a language expert who corrects ONLY grammar in mixed Portuguese-English text.

IMPORTANT: Do NOT translate any words. Keep Portuguese words in Portuguese and English words in English.
Only fix grammar structure, word order, and flow. Remove incomplete phrases like "...".

Example input: "Eu quero falar de outra coisa, por exemplo... the kitchen and what I'm going to e cozinhar para jantar."
Example output: "Eu quero falar de outra coisa, por exemplo the kitchen and what I'm going to cozinhar para jantar."

Input: "{transcript}"
Output:"""
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a grammar expert. Fix ONLY grammar, NEVER translate. Keep original languages intact."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        temperature=0.6
    )
    
    return response.choices[0].message.content.strip()

@app.post("/process-recording")
async def process_recording(
    audio: UploadFile = File(...),
    spans: str = Form(...),
    duration: str = Form(...)
):
    """
    Process audio recording using segmented-parallel approach.
    
    Splits audio into segments based on user-provided spans and transcribes
    each segment in parallel using Whisper API with language-specific prompts.
    
    Args:
        audio: Audio file upload
        spans: JSON string of language spans (Portuguese and English with timestamps)
        duration: Recording duration in seconds
        
    Returns:
        Dict containing transcript and performance metrics
    """
    # Initialize temp file path for cleanup
    temp_file_path = None
    
    try:
        # Start performance tracking
        start_transcription = time.time()

        # Parse input data
        parsing_start = time.time()
        spans_data = json.loads(spans)
        duration_float = float(duration)
        audio_content = await audio.read()
        client = OpenAI()
        parsing_end = time.time()

        # Create temporary file for audio processing
        file_setup_start = time.time()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(audio_content)
            temp_file_path = temp_file.name
        file_setup_end = time.time()

        # Step 1: Load audio and get sample rate
        audio_loading_start = time.time()
        audio_data, sample_rate = librosa.load(temp_file_path, sr=None)
        audio_loading_end = time.time()
        
        # Step 2: Create segments from spans
        segmentation_start = time.time()
        segments = create_segments_from_spans(audio_data, spans_data, sample_rate)
        segmentation_end = time.time()
        
        logger.info(f"Created {len(segments)} segments from {len(spans_data)} spans")

        async def transcribe_segment_parallel(segment, client):
            """Transcribe a single segment in parallel."""
            segment_start = time.time()
            try:
                # Create temporary file for this segment
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_segment_file:
                    temp_segment_path = temp_segment_file.name
                    
                    # Save segment audio to file
                    soundfile.write(temp_segment_path, segment['audio_data'], segment['sample_rate'])
                    
                    # Map language to Whisper language code
                    language_map = {
                        'portuguese': 'pt',
                        'english': 'en'
                    }
                    
                    # Transcribe segment with language parameter
                    with open(temp_segment_path, "rb") as audio_file:
                        transcript = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            language=language_map[segment['language']]
                        )
                    
                    # Clean up segment file
                    os.unlink(temp_segment_path)
                    
                    segment_end = time.time()
                    segment_duration = segment_end - segment_start
                    logger.info(f"Segment {segment['index']} ({segment['language']}) completed in {segment_duration:.2f}s: '{transcript.text[:50]}...'")
                    
                    return {
                        'start_time': segment['start_time'],
                        'end_time': segment['end_time'],
                        'language': segment['language'],
                        'text': transcript.text,
                        'processing_time': segment_duration
                    }
                    
            except Exception as e:
                logger.error(f"Segment {segment['index']} transcription failed: {str(e)}")
                return {
                    'start_time': segment['start_time'],
                    'end_time': segment['end_time'],
                    'language': segment['language'],
                    'text': f"[ERROR: {str(e)}]"
                }

        # Step 3: Transcribe all segments in parallel
        transcription_start = time.time()
        transcription_tasks = [
            transcribe_segment_parallel(segment, client) for segment in segments
        ]
        transcription_results = await asyncio.gather(*transcription_tasks)
        transcription_end = time.time()

        # Step 4: Sort results by start time and combine
        transcription_results.sort(key=lambda x: x['start_time'])
        full_transcript = " ".join([result['text'] for result in transcription_results])

        # Step 4.5: Grammar correction pass ✨
        grammar_start = time.time()
        corrected_transcript = apply_grammar_correction(full_transcript)
        grammar_end = time.time()

        # Step 5: Calculate final timing
        end_transcription = time.time()

        logger.info(f"Transcription completed: '{full_transcript[:100]}...'")

        # Return results with detailed timing
        results = {
            'transcript': corrected_transcript,  # ← Now the corrected version
            'raw_transcript': full_transcript,   # ← Keep original for comparison
            'duration': duration_float,
            'spans_count': len(spans_data),
            'segments_count': len(segments),
            'total_time': end_transcription - start_transcription,
            'parsing_time': parsing_end - parsing_start,
            'file_setup_time': file_setup_end - file_setup_start,
            'audio_loading_time': audio_loading_end - audio_loading_start,
            'segmentation_time': segmentation_end - segmentation_start,
            'transcription_time': transcription_end - transcription_start,
            'grammar_correction_time': grammar_end - grammar_start,  # ← New timing
            'segment_timings': [result['processing_time'] for result in transcription_results]
        }

        save_transcript(results)

        return results
            
    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        return {
            "error": f"Transcription failed: {str(e)}",
            "duration": duration_float,
            "spans_count": len(spans_data)
        }

    finally:
        # Clean up temporary file (safe even if temp_file_path wasn't created)
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)