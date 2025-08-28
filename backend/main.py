#region IMPORTS
# Standard library
import datetime
from datetime import datetime
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
        all_results.append(results)
        
        # Save back to file
        with open(file_path, "w") as file:
            json.dump(all_results, file, indent=2)
            
        
    except Exception as e:
        logger.error("Failed to save transcript", extra={"error": str(e), "file_path": file_path})
        # Don't crash the main function if saving fails
        pass
#endregion

#region API ENDPOINTS

#region Utility Endpoints
@app.get("/")
async def root():
    return FileResponse("../frontend/index.html")

@app.get("/api/health")
async def health():
    return {"message": "Portuguese gap-capture backend"}
#endregion

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
        segmentation_end = time.time()
        
        logger.info(f"Created {len(segments)} segments from {len(spans_data)} spans")

        # Step 3: Transcribe all segments in parallel
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
                    
                    return {
                        'start_time': segment['start_time'],
                        'end_time': segment['end_time'],
                        'language': segment['language'],
                        'text': transcript.text,
                        'processing_time': segment_duration
                    }
                    
            except Exception as e:
                logger.error(f"Segment {segment['index']} transcription failed", extra={"error": str(e), "language": segment['language']})
                return {
                    'start_time': segment['start_time'],
                    'end_time': segment['end_time'],
                    'language': segment['language'],
                    'text': f"[ERROR: {str(e)}]"
                }

        transcription_start = time.time()
        transcription_tasks = [
            transcribe_segment_parallel(segment, client) for segment in segments
        ]
        transcription_results = await asyncio.gather(*transcription_tasks)
        transcription_end = time.time()

        # Step 4: Sort results by start time and combine
        transcription_results.sort(key=lambda x: x['start_time'])
        full_transcript = " ".join([result['text'] for result in transcription_results])

        # Step 5: Extract English segments for translation
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

        # Step 6: Translate English segments
        translation_start = time.time()
        translations = []
        
        if english_segments:
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

                English: {segment['clean_text']}
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
        
        translation_end = time.time()

        # Step 7: Grammar correction pass ✨
        grammar_start = time.time()
        
        prompt = f"""
        You are a language expert who corrects ONLY grammar in mixed Portuguese-English text.

        IMPORTANT: Do NOT translate any words. Keep Portuguese words in Portuguese and English words in English.
        Only fix grammar structure, word order, and flow. Remove incomplete phrases like "...".

        Example input: Eu quero falar de outra coisa, por exemplo... the kitchen and what I'm going to e cozinhar para jantar.
        Example output: Eu quero falar de outra coisa, por exemplo the kitchen and what I'm going to cozinhar para jantar.

        NEVER show "" (quotation marks) or ... (ellipsis) in the output.

        Input: "{full_transcript}"
        Output:"""
            
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a grammar expert. Fix ONLY grammar, NEVER translate. Keep original languages intact."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=300,
                temperature=0.1
            )
            
            corrected_transcript = response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error("Grammar correction failed", extra={"input_length": len(full_transcript), "error": str(e)})
            raise
        
        grammar_end = time.time()

        # Step 8: Calculate final timing
        end_transcription = time.time()

        # Step 8: Translate full sentences from transcript
        def translate_full_sentences(transcript: str, client: OpenAI):

            sentences_translations = []
            original_sentences = [s.strip() for s in transcript.replace('!', '.').replace('?', '.').split('.') if s.strip()]

            for sentence in original_sentences:
                prompt = f"""
                Translate this sentence which is in portuguese but contains english words to Portuguese. Provide only the Portuguese translation, no explanations.
                
                please leave the punctuation unchanged. just translate the words.

                The only thing that should change from input to output is the translation of the english words to portuguese.
                """

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

                sentences_translations.append({
                    'english': sentence,
                    'portuguese': portuguese_translation
                })

                return sentences_translations, original_sentences

        sentences_translations, original_sentences = translate_full_sentences(full_transcript, client)


        # Step 9: Create results with detailed timing
        results = {
            # Metadata
            'timestamp': datetime.now().isoformat(),
            
            # Final processed transcripts
            'transcript': corrected_transcript,        # Grammar-corrected final version
            'raw_transcript': full_transcript,         # Original unprocessed transcript
            'corrected_transcript': corrected_transcript,  # Grammar-corrected (duplicate)
            'full_transcript': full_transcript,        # Original (duplicate)
            
            # Segment information
            'english_segments': english_segments,      # English-only segments
            'translations': translations,              # Portuguese translations
            'english_segments': english_segments,      # English segments (duplicate)
            'translations': translations,              # Translations (duplicate)
            
            # Audio metadata
            'duration': duration_float,               # Recording length in seconds
            'spans_count': len(spans_data),          # Number of language spans
            'segments_count': len(segments),         # Total segments processed

            # Full sentence translations tests
            'original_sentences': original_sentences, # Full sentences
            'sentence_translations': sentences_translations, # Full sentence translations

            # Performance metrics
            'total_time': end_transcription - start_transcription,  # Overall processing time
            'parsing_time': parsing_end - parsing_start,            # Input parsing
            'file_setup_time': file_setup_end - file_setup_start,  # File preparation
            'audio_loading_time': audio_loading_end - audio_loading_start,  # Audio loading
            'segmentation_time': segmentation_end - segmentation_start,     # Audio segmentation
            'transcription_time': transcription_end - transcription_start,  # Speech-to-text
            'translation_time': translation_end - translation_start,        # Translation
            'grammar_correction_time': grammar_end - grammar_start,         # Grammar fixes
            'segment_timings': [result['processing_time'] for result in transcription_results], # Per-segment timing
        }

        save_transcript(results)
        
        logger.info("Recording processed successfully", extra={
            "duration": duration_float,
            "segments_count": len(segments),
            "english_segments_count": len(english_segments)
        })

        return results

    except Exception as e:
        logger.error("Transcription failed", extra={
            "error": str(e),
            "duration": duration_float,
            "spans_count": len(spans_data),
            "error_type": type(e).__name__
        })
        return {
            "error": f"Transcription failed: {str(e)}",
            "duration": duration_float,
            "spans_count": len(spans_data)
        }
    
    finally: # Clean up temporary file (safe even if temp_file_path wasn't created)
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

#endregion

