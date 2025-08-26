#region IMPORTS
# Standard library
import json
import os
import tempfile
import time
import asyncio

# Third-party
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from openai import OpenAI
import soundfile 
import librosa

# Local
from config.settings import settings
from config.logging import logger
from middleware.cors import setup_cors
#endregion

#region CONFIGURATION
from config.settings import settings
from config.logging import logger
from middleware.cors import setup_cors
#endregion

#region APP SETUP
app = FastAPI(title=settings.APP_TITLE, version=settings.APP_VERSION)
app.mount("/static", StaticFiles(directory=settings.STATIC_FILES_DIR), name="static")
setup_cors(app)
#endregion

#region UTILITY FUNCTIONS
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
            "segment_timings": results["segment_timings"],
            "english_segments": results["english_segments"],
            "translations": results["translations"],
            "corrected_transcript": results["corrected_transcript"]
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
    
    logger.info(f"=== GRAMMAR CORRECTION INPUT === '{transcript}'")
    
    prompt = f"""
    You are a language expert who corrects ONLY grammar in mixed Portuguese-English text.

    IMPORTANT: Do NOT translate any words. Keep Portuguese words in Portuguese and English words in English.
    Only fix grammar structure, word order, and flow. Remove incomplete phrases like "...".

    Example input: Eu quero falar de outra coisa, por exemplo... the kitchen and what I'm going to e cozinhar para jantar.
    Example output: Eu quero falar de outra coisa, por exemplo the kitchen and what I'm going to cozinhar para jantar.

    NEVER show "" (quotation marks) or ... (ellipsis) in the output.

    Input: "{transcript}"
    Output:"""
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a grammar expert. Fix ONLY grammar, NEVER translate. Keep original languages intact."},
            {"role": "user", "content": prompt}
        ],
        max_completion_tokens=300,
        temperature=0.1
    )
    
    corrected_text = response.choices[0].message.content.strip()
    logger.info(f"=== GRAMMAR CORRECTION OUTPUT === '{corrected_text}'")
    
    return corrected_text

def extract_english_segments(transcription_results):
    """
    Extract English segments from transcription results.
    
    Args:
        transcription_results: List of segment results from transcription
        
    Returns:
        List of English segments with timing, original text, and clean text
    """
    english_segments = []
    
    for result in transcription_results:
        if result['language'] == 'english':
            original_text = result['text']
            
            # Create clean version for matching after grammar correction
            clean_text = original_text.strip()
            # Remove common punctuation that might be removed by grammar correction
            clean_text = clean_text.rstrip('.,;:!?')
            # Normalize spacing
            clean_text = ' '.join(clean_text.split())
            
            english_segments.append({
                'text': original_text,
                'clean_text': clean_text,
                'start_time': result['start_time'],
                'end_time': result['end_time']
            })
    
    return english_segments

def translate_english_segments(english_segments):
    """
    Translate English segments to Portuguese.
    
    Args:
        english_segments: List of English segments with text and timing
        
    Returns:
        List of translation pairs (English -> Portuguese)
    """
    if not english_segments:
        return []
    
    client = OpenAI()
    translations = []
    
    for segment in english_segments:
        prompt = f"""
    Translate this English phrase to Portuguese. Provide only the Portuguese translation, no explanations.

    Do not include any of the following in the output:
    - Double quotes ("")
    - Single quotes ('')
    - Ellipsis (...)
    - Commas (,)
    - Periods (.)
    - Any other punctuation marks

    English: {segment['text']}
    Portuguese:"""
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a Portuguese translator. Provide only the translation, no explanations."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.1
        )
        
        portuguese_translation = response.choices[0].message.content.strip()
        
        translations.append({
            'english': segment['text'],  # Original text for display
            'english_clean': segment['clean_text'],  # Clean text for matching
            'portuguese': portuguese_translation,
            'start_time': segment['start_time'],
            'end_time': segment['end_time']
        })
    
    return translations
#endregion

#region API ENDPOINTS

@app.get("/")
async def root():
    return FileResponse("../frontend/index.html")

@app.get("/api/health")
async def health():
    return {"message": "Portuguese gap-capture backend"}
    

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
        
        # Log each segment before combining
        logger.info("=== SEGMENTS BEFORE COMBINING ===")
        for i, result in enumerate(transcription_results):
            logger.info(f"Segment {i}: [{result['language']}] '{result['text']}'")
        
        full_transcript = " ".join([result['text'] for result in transcription_results])
        logger.info(f"=== COMBINED TRANSCRIPT === '{full_transcript}'")

        # Step 4.5: Extract English segments for translation
        english_segments = extract_english_segments(transcription_results)
        logger.info(f"Extracted {len(english_segments)} English segments for translation")

        # Step 4.6: Translate English segments
        translation_start = time.time()
        translations = translate_english_segments(english_segments)
        translation_end = time.time()
        logger.info(f"Translated {len(translations)} English segments in {translation_end - translation_start:.2f}s")

        # Step 4.7: Grammar correction pass ✨
        grammar_start = time.time()
        corrected_transcript = apply_grammar_correction(full_transcript)
        grammar_end = time.time()

        # Step 5: Calculate final timing
        end_transcription = time.time()

        logger.info(f"Transcription completed: '{full_transcript[:100]}...'")

        # Return results with detailed timing
        results = {
            'transcript': corrected_transcript,
            'raw_transcript': full_transcript,
            'english_segments': english_segments,
            'translations': translations,
            'duration': duration_float,
            'spans_count': len(spans_data),
            'segments_count': len(segments),
            'total_time': end_transcription - start_transcription,
            'parsing_time': parsing_end - parsing_start,
            'file_setup_time': file_setup_end - file_setup_start,
            'audio_loading_time': audio_loading_end - audio_loading_start,
            'segmentation_time': segmentation_end - segmentation_start,
            'transcription_time': transcription_end - transcription_start,
            'translation_time': translation_end - translation_start, 
            'grammar_correction_time': grammar_end - grammar_start,
            'segment_timings': [result['processing_time'] for result in transcription_results],
            'english_segments': english_segments,
            'translations': translations,
            'corrected_transcript': corrected_transcript,
            'full_transcript': full_transcript
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
    
    finally: # Clean up temporary file (safe even if temp_file_path wasn't created)
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

#endregion