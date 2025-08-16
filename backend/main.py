from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import os
import tempfile
import logging
from openai import OpenAI
from typing import List, Dict
import librosa
import soundfile as sf
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Portuguese Gap-Capture API", version="1.0.0")

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:3000", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

def split_audio_by_spans(audio_path: str, spans: List[Dict], total_duration: float) -> List[Dict]:
    """
    Split audio into segments using librosa - includes all parts of the audio
    """
    # Load audio file
    y, sr = librosa.load(audio_path, sr=None)
    
    segments = []
    segment_index = 0
    
    # Sort spans by start time
    sorted_spans = sorted(spans, key=lambda x: x.get('start', 0))
    
    current_time = 0
    
    for i, span in enumerate(sorted_spans):
        span_start = span.get('start', 0)
        span_end = span.get('end', total_duration)
        
        # Add Portuguese segment before this span (if there's a gap)
        if span_start > current_time:
            portuguese_start_sample = int(current_time * sr)
            portuguese_end_sample = int(span_start * sr)
            portuguese_audio = y[portuguese_start_sample:portuguese_end_sample]
            
            segments.append({
                'index': segment_index,
                'start_time': current_time,
                'end_time': span_start,
                'language': 'portuguese',
                'audio_data': portuguese_audio,
                'sample_rate': sr
            })
            segment_index += 1
        
        # Add the English span
        english_start_sample = int(span_start * sr)
        english_end_sample = int(span_end * sr)
        english_audio = y[english_start_sample:english_end_sample]
        
        segments.append({
            'index': segment_index,
            'start_time': span_start,
            'end_time': span_end,
            'language': 'english',
            'audio_data': english_audio,
            'sample_rate': sr
        })
        segment_index += 1
        
        current_time = span_end
    
    # Add final Portuguese segment if there's remaining audio
    if current_time < total_duration:
        final_start_sample = int(current_time * sr)
        final_end_sample = int(total_duration * sr)
        final_audio = y[final_start_sample:final_end_sample]
        
        segments.append({
            'index': segment_index,
            'start_time': current_time,
            'end_time': total_duration,
            'language': 'portuguese',
            'audio_data': final_audio,
            'sample_rate': sr
        })
    
    return segments

@app.post("/process-recording")
async def process_recording(
    audio: UploadFile = File(...),
    spans: str = Form(...),
    duration: str = Form(...)
):
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
        
        for segment in segments:
            logger.info(f"Transcribing segment {segment['index']} ({segment['language']})")
            # Save segment to temporary file using soundfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as segment_file:
                sf.write(segment_file.name, segment['audio_data'], segment['sample_rate'])
                
                language_code = "pt" if segment['language'] == 'portuguese' else "en"

                with open(segment_file.name, "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language=language_code
                    )
                
                transcriptions.append({
                    'segment_index': segment['index'],
                    'language': segment['language'],
                    'text': transcript.text,
                    'start_time': segment['start_time'],
                    'end_time': segment['end_time']
                })
                
                logger.info(f"Segment {segment['index']} transcribed: '{transcript.text[:50]}...'")
                os.unlink(segment_file.name)

        full_transcript = " ".join([t['text'] for t in transcriptions])
        logger.info(f"Processing completed successfully. Full transcript: {full_transcript[:100]}...")

        return {
            "message": "success",
            "duration": duration_float,
            "spans": spans_data,
            "transcriptions": transcriptions,
            "full_transcript": full_transcript
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