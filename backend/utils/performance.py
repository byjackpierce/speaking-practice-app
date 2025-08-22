"""
Performance Utilities
====================

Provides standardized performance tracking and metrics creation.
Used across different transcription approaches for consistent timing measurements.
"""

import time
from datetime import datetime
from typing import Dict, Any

def create_performance_metrics(
    duration_seconds: float,
    segments_count: int,
    spans_count: int,
    approach: str,
    processing_start: float,
    audio_setup_complete: float = None,
    transcription_complete: float = None
) -> Dict[str, Any]:
    """
    Create standardized performance metrics
    """
    timing = {
        "total_time": transcription_complete - processing_start if transcription_complete else 0,
    }
    
    if audio_setup_complete:
        timing["audio_setup_time"] = audio_setup_complete - processing_start
    
    if transcription_complete and audio_setup_complete:
        timing["transcription_time"] = transcription_complete - audio_setup_complete
    
    return {
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": duration_seconds,
        "segments_count": segments_count,
        "spans_count": spans_count,
        "approach": approach,
        "timing": timing
    }
