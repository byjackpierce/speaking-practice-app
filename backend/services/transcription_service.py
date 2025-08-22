"""
Transcription Service
====================

Handles OpenAI API interactions for audio transcription and translation.
Provides both segmented and simple transcription approaches.
"""

from openai import OpenAI
from typing import List, Dict
from config.logging import logger

def transcribe_segment(segment: Dict, client: OpenAI) -> Dict:
    """
    Transcribe a single audio segment and optionally translate if it's English
    """
    language_code = "pt" if segment['language'] == 'portuguese' else "en"
    
    with open(segment['temp_file_path'], "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=language_code
        )

    result = {
        'segment_index': segment['index'],
        'language': segment['language'],
        'text': transcript.text,
        'translation': None,
        'start_time': segment['start_time'],
        'end_time': segment['end_time']
    }

    # Add translation for English segments
    if segment['language'] == 'english':
        try:
            translation_response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful Portuguese translator. Translate the given English text to natural Portuguese."},
                    {"role": "user", "content": f"Translate this to Portuguese: {transcript.text}"}
                ]
            )
            result['translation'] = translation_response.choices[0].message.content.strip()
            logger.info(f"Translation generated: '{transcript.text}' → '{result['translation']}'")
        except Exception as e:
            logger.error(f"Translation failed: {str(e)}")
            result['translation'] = "Translation error"

    logger.info(f"Segment {segment['index']} transcribed: '{transcript.text[:50]}...'")
    return result

def transcribe_simple(audio_file_path: str, client: OpenAI) -> str:
    """
    Transcribe entire audio file as Portuguese (simple approach)
    """
    with open(audio_file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language='pt'
        )
    
    logger.info(f"Simple transcription completed: '{transcript.text[:100]}...'")
    return transcript.text
