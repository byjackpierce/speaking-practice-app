"""
Audio Processing Service
=======================

Handles audio file manipulation, segmentation, and temporary file management.
Provides functions for splitting audio by language spans and managing temporary files.
"""

import librosa
import soundfile as sf
import tempfile
import os
from typing import List, Dict
from config.logging import logger

def split_audio_by_spans(audio_path: str, spans: List[Dict], total_duration: float) -> List[Dict]:
    """
    Split audio into segments using librosa - includes all parts of the audio
    """
    # Load audio file with error handling
    try:
        y, sr = librosa.load(audio_path, sr=None)
        if sr is None:
            # Fallback to default sample rate
            y, sr = librosa.load(audio_path, sr=22050)
    except Exception as e:
        logger.error(f"Failed to load audio file: {e}")
        raise Exception(f"Audio file could not be loaded: {e}")
    
    if y is None or len(y) == 0:
        raise Exception("Audio file is empty or corrupted")
    
    segments = []
    segment_index = 0
    
    # Sort spans by start time
    sorted_spans = sorted(spans, key=lambda x: x.get('start', 0))
    
    current_time = 0
    
    for span in sorted_spans:
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

def save_audio_segment(segment: Dict) -> str:
    """
    Save an audio segment to a temporary file and return the file path
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as segment_file:
        sf.write(segment_file.name, segment['audio_data'], segment['sample_rate'])
        return segment_file.name

def cleanup_temp_file(file_path: str):
    """
    Clean up a temporary file
    """
    if os.path.exists(file_path):
        os.unlink(file_path)
        logger.info("Cleaned up temporary audio file")
