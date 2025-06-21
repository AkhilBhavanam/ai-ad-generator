import os
import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import timedelta, datetime

from backend.core.models import AdScript

logger = logging.getLogger(__name__)

@dataclass
class SubtitleSegment:
    """Subtitle segment with timing information"""
    text: str
    start_time: float
    end_time: float
    index: int

class SubtitleGenerator:
    """Handles subtitle generation, timing, and SRT creation"""
    
    def __init__(self, temp_dir: str = "temp_assets"):
        self.temp_dir = temp_dir
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Speech timing parameters
        self.words_per_minute = 150  # Average speech rate
        self.pause_after_sentence = 0.5  # Seconds
        self.pause_after_comma = 0.2  # Seconds
    
    def generate_forced_alignment(self, ad_script: AdScript, total_duration: float) -> List[SubtitleSegment]:
        """Generate forced alignment timing for subtitle segments"""
        try:
            # Combine script parts
            script_parts = [
                ad_script.hook,
                f"{ad_script.problem} {ad_script.solution}",
                " and ".join(ad_script.benefits[:2]) if ad_script.benefits else "",
                ad_script.call_to_action
            ]
            
            # Filter out empty parts
            script_parts = [part.strip() for part in script_parts if part.strip()]
            
            # Clean up the script
            full_script = ". ".join(script_parts)
            full_script = self._clean_script_for_speech(full_script)
            
            # Split into segments and phrases
            segments = self._split_into_segments(full_script)
            
            # Calculate timing for each segment
            subtitle_segments = []
            current_time = 0.0
            
            total_words = sum(len(segment.split()) for segment in segments)
            words_per_second = total_words / total_duration
            
            logger.info(f"Estimated speech rate: {words_per_second:.2f} words/second")
            
            for i, segment in enumerate(segments):
                words_in_segment = len(segment.split())
                
                # Calculate duration based on word count
                segment_duration = words_in_segment / words_per_second
                
                # Add pauses for punctuation
                if segment.endswith('.') or segment.endswith('!') or segment.endswith('?'):
                    segment_duration += self.pause_after_sentence
                elif ',' in segment:
                    segment_duration += self.pause_after_comma * segment.count(',')
                
                end_time = current_time + segment_duration
                
                # Ensure we don't exceed total duration
                if end_time > total_duration:
                    end_time = total_duration
                
                subtitle_segments.append(SubtitleSegment(
                    start_time=current_time,
                    end_time=end_time,
                    text=segment,
                    index=i
                ))
                
                current_time = end_time
                
                logger.debug(f"Segment {i+1}: {current_time-segment_duration:.2f}s - {end_time:.2f}s: '{segment[:50]}...'")
            
            return subtitle_segments
            
        except Exception as e:
            logger.error(f"Error generating forced alignment: {str(e)}")
            return []
    
    def _split_into_segments(self, text: str) -> List[str]:
        """Split text into meaningful segments for subtitles"""
        # Split by sentences first
        sentences = re.split(r'[.!?]+', text)
        segments = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # If sentence is too long, split by commas or conjunctions
            if len(sentence.split()) > 8:
                # Split by commas
                parts = sentence.split(',')
                if len(parts) > 1:
                    for part in parts:
                        part = part.strip()
                        if part:
                            segments.append(part)
                else:
                    # Split by conjunctions
                    conjunctions = [' and ', ' but ', ' or ', ' so ', ' yet ']
                    remaining = sentence
                    
                    for conj in conjunctions:
                        if conj in remaining:
                            parts = remaining.split(conj, 1)
                            segments.append(parts[0].strip())
                            remaining = parts[1].strip()
                            break
                    
                    if remaining:
                        segments.append(remaining)
            else:
                segments.append(sentence)
        
        # Filter out very short segments and combine them
        final_segments = []
        current_segment = ""
        
        for segment in segments:
            if len(segment.split()) < 3 and current_segment:
                current_segment += " " + segment
            else:
                if current_segment:
                    final_segments.append(current_segment.strip())
                current_segment = segment
        
        if current_segment:
            final_segments.append(current_segment.strip())
        
        return final_segments
    
    async def create_srt_file(self, subtitle_segments: List[SubtitleSegment], session_id: str) -> str:
        """Create SRT subtitle file from segments"""
        try:
            srt_path = os.path.join(self.temp_dir, f"{session_id}_subtitles.srt")
            
            with open(srt_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(subtitle_segments, 1):
                    # Convert time to SRT format
                    start_time = self._seconds_to_srt_time(segment.start_time)
                    end_time = self._seconds_to_srt_time(segment.end_time)
                    
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{segment.text}\n\n")
            
            logger.info(f"Created SRT file with {len(subtitle_segments)} segments")
            return srt_path
            
        except Exception as e:
            logger.error(f"Error creating SRT file: {str(e)}")
            return ""
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        td = timedelta(seconds=seconds)
        hours, remainder = divmod(td.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = int((seconds % 1) * 1000)
        
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d},{milliseconds:03d}"
    
    def _clean_script_for_speech(self, script: str) -> str:
        """Clean script text for speech processing"""
        # Remove excessive punctuation
        script = re.sub(r'[!]{2,}', '!', script)
        script = re.sub(r'[?]{2,}', '?', script)
        script = re.sub(r'[.]{2,}', '.', script)
        
        # Clean up multiple spaces
        script = re.sub(r'\s+', ' ', script)
        
        return script.strip() 