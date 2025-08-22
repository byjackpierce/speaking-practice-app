from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import os
import tempfile
import time
import librosa
from openai import OpenAI

"""
Portuguese Gap-Capture API
==========================

FastAPI application for processing mixed Portuguese-English audio recordings.
Provides both segmented and simple transcription approaches with performance comparison.

Endpoints:
- POST /process-recording: Segmented transcription with language detection
- POST /process-recording-simple: Simple Portuguese transcription
- GET /: Frontend interface
- GET /api/health: Health check
"""

# Import our modular components
from config.settings import settings
from config.logging import logger
from middleware.cors import setup_cors
from services.audio_service import split_audio_by_spans, save_audio_segment, cleanup_temp_file
from services.transcription_service import transcribe_segment, transcribe_simple
from utils.performance import create_performance_metrics

# Create FastAPI app
app = FastAPI(title=settings.APP_TITLE, version=settings.APP_VERSION)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory=settings.STATIC_FILES_DIR), name="static")

# Setup CORS middleware
setup_cors(app)



@app.post("/process-recording")
async def process_recording(
    audio: UploadFile = File(...),
    spans: str = Form(...),
    duration: str = Form(...)
):
    """
    Process audio recording using segmented approach.
    
    Splits audio into Portuguese and English segments based on user-provided spans,
    transcribes each segment separately, and provides translations for English parts.
    
    Args:
        audio: Audio file upload
        spans: JSON string of language span timestamps
        duration: Recording duration in seconds
        
    Returns:
        Dict containing transcriptions, translations, and performance metrics
    """
    processing_start = time.time()
    logger.info(f"Processing recording: {audio.filename}, duration: {duration}s")
    
    spans_data = json.loads(spans)
    duration_float = float(duration)
    
    logger.info(f"Found {len(spans_data)} language spans")

    client = OpenAI()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        content = await audio.read()
        temp_file.write(content)
        temp_file_path = temp_file.name
        logger.info(f"Saved audio to temporary file: {temp_file_path}")

    try:
        if not spans_data:
            logger.info("No spans detected, treating entire audio as Portuguese")
            # If no spans, treat entire audio as Portuguese
            segments = [{
                'index': 0,
                'start_time': 0,
                'end_time': duration_float,
                'language': 'portuguese',
                'audio_data': librosa.load(temp_file_path, sr=None)[0],
                'sample_rate': librosa.load(temp_file_path, sr=None)[1]
            }]
        else:
            logger.info("Splitting audio into segments")
            segments = split_audio_by_spans(temp_file_path, spans_data, duration_float)

        logger.info(f"Created {len(segments)} audio segments")
        transcriptions = []
        
        audio_setup_complete = time.time()

        for segment in segments:
            logger.info(f"Transcribing segment {segment['index']} ({segment['language']})")
            # Save segment to temporary file
            segment['temp_file_path'] = save_audio_segment(segment)
            
            # Transcribe segment
            transcription_result = transcribe_segment(segment, client)
            transcriptions.append(transcription_result)
            
            # Clean up segment file
            cleanup_temp_file(segment['temp_file_path'])

        full_transcript = " ".join([t['text'] for t in transcriptions])
        logger.info(f"Processing completed successfully. Full transcript: {full_transcript[:100]}...")
        
        transcription_complete = time.time()

        performance_metrics = create_performance_metrics(
            duration_float, len(segments), len(spans_data), "segmented",
            processing_start, audio_setup_complete, transcription_complete
        )

        return {
            "message": "success",
            "duration": duration_float,
            "spans": spans_data,
            "transcriptions": transcriptions,
            "full_transcript": full_transcript,
            "performance_metrics": performance_metrics
        }

    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        return {
            "error": f"Transcription failed: {str(e)}",
            "duration": duration_float,
            "spans": spans_data
        }

    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            logger.info("Cleaned up temporary audio file")

@app.post("/process-recording-simple")
async def process_recording_simple(
    audio: UploadFile = File(...),
    spans: str = Form(...),
    duration: str = Form(...)
):
    """
    Process audio recording using simple approach.
    
    Transcribes entire audio as Portuguese for better grammar flow.
    Faster than segmented approach but may translate English words.
    
    Args:
        audio: Audio file upload
        spans: JSON string of language span timestamps (not used in simple approach)
        duration: Recording duration in seconds
        
    Returns:
        Dict containing full transcript and performance metrics
    """
    try:
            
        processing_start_time = time.time()

        spans_data = json.loads(spans)
        duration_float = float(duration)

        client = OpenAI()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
            logger.info(f"Saved audio to temporary file: {temp_file_path}")
            logger.info("Processing entire file")


            # Use the transcription service
            transcript_text = transcribe_simple(temp_file_path, client)

            processing_end_time = time.time()

            performance_metrics = create_performance_metrics(
                duration_float, 1, len(spans_data), "simple_portuguese",
                processing_start_time, processing_start_time, processing_end_time
            )

            return {
                "message": "success",
                "duration": duration_float,
                "spans": spans_data,
                "transcriptions": None,
                "full_transcript": transcript_text,
                "performance_metrics": performance_metrics
            }

    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        return {
            "error": f"Transcription failed: {str(e)}",
            "duration": duration_float,
            "spans": spans_data
        }


    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            logger.info("Cleaned up temporary audio file")


@app.get("/")
async def root():
    return FileResponse("../frontend/index.html")

@app.get("/api/health")
async def health():
    return {"message": "Portuguese gap-capture backend"}