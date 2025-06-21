import os
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import ImageClip, CompositeVideoClip, VideoClip
from moviepy.video.fx import resize

logger = logging.getLogger(__name__)

@dataclass
class WordTiming:
    """Word-level timing information"""
    word: str
    start: float
    end: float
    confidence: float = 1.0

@dataclass
class KaraokeSegment:
    """Karaoke segment with word timings"""
    full_text: str
    start_time: float
    end_time: float
    words: List[WordTiming]

class KaraokeTextRenderer:
    """
    Specialized text renderer for karaoke-style subtitles with word-by-word highlighting.
    Each word is highlighted as it's spoken, creating a karaoke effect.
    """
    
    def __init__(self, temp_dir: str = "temp_assets"):
        self.temp_dir = temp_dir
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Karaoke styling configuration
        self.highlight_colors = {
            "default": "#FFD700",      # Gold for highlighted words
            "energetic": "#FF4081",    # Pink for energetic content
            "professional": "#00BCD4", # Cyan for professional content
            "warm": "#FF8A65",         # Orange for warm content
        }
        
        self.text_colors = {
            "default": "#FFFFFF",      # White for unhighlighted text
            "shadow": "#000000",       # Black for text shadow
            "background": "#000000"    # Black for background
        }
    
    def create_karaoke_subtitle_clips(self, segments: List[KaraokeSegment], 
                                    width: int, height: int, colors: Dict[str, str],
                                    style: str = "default") -> List[VideoClip]:
        """
        Create karaoke-style subtitle clips with word-by-word highlighting.
        
        Args:
            segments: List of karaoke segments with word-level timing
            width: Video width
            height: Video height 
            colors: Color scheme dictionary
            style: Visual style (default, energetic, professional, warm)
            
        Returns:
            List of VideoClip objects for karaoke subtitles
        """
        try:
            # Use sliding karaoke for better visual experience
            return self._create_sliding_karaoke_clips(segments, width, height, colors, style)
            
        except Exception as e:
            logger.error(f"Error creating karaoke subtitle clips: {str(e)}")
            return []
    
    def _create_sliding_karaoke_clips(self, segments: List[KaraokeSegment], 
                                    width: int, height: int, colors: Dict[str, str],
                                    style: str = "default") -> List[VideoClip]:
        """Create sliding karaoke clips that show 3-5 words at a time with no black bars"""
        try:
            karaoke_clips = []
            highlight_color = self.highlight_colors.get(style, self.highlight_colors["default"])
            
            # FIXED: Better responsive font sizing
            if width >= 1920:  # 4K/Full HD
                font_size = 32
            elif width >= 1280:  # HD
                font_size = 26
            elif width >= 854:   # SD
                font_size = 22
            else:  # Very small
                font_size = 18
            
            font = self._load_font(font_size)
            
            for segment in segments:
                # Create sliding word groups (3-5 words per group)
                sliding_clips = self._create_sliding_word_groups(
                    segment, width, height, font, highlight_color, style
                )
                karaoke_clips.extend(sliding_clips)
            
            logger.info(f"Created {len(karaoke_clips)} sliding karaoke clips")
            return karaoke_clips
            
        except Exception as e:
            logger.error(f"Error creating sliding karaoke clips: {str(e)}")
            return []
    
    def _create_sliding_word_groups(self, segment: KaraokeSegment, width: int, height: int,
                                  font, highlight_color: str, style: str) -> List[VideoClip]:
        """Create sliding groups based on sentence boundaries for natural flow"""
        try:
            clips = []
            words = segment.words
            
            # Split words into sentence groups
            sentence_groups = self._split_words_by_sentences(words, segment.full_text)
            
            for sentence_group in sentence_groups:
                if not sentence_group:
                    continue
                
                # Calculate timing for this sentence
                group_start = sentence_group[0].start
                group_end = sentence_group[-1].end
                group_duration = group_end - group_start
                
                if group_duration <= 0:
                    continue
                
                # Create sliding clip for this sentence
                group_clip = self._create_word_group_clip(
                    sentence_group, width, height, font, highlight_color, 
                    group_duration, style
                )
                
                if group_clip:
                    # Position and time the clip
                    group_clip = group_clip.set_start(group_start - segment.start_time)
                    clips.append(group_clip)
            
            return clips
            
        except Exception as e:
            logger.error(f"Error creating sliding sentence groups: {str(e)}")
            return []
    
    def _split_words_by_sentences(self, words: List[WordTiming], full_text: str) -> List[List[WordTiming]]:
        """Split word timings into sentence groups based on sentence boundaries"""
        try:
            # Find sentence boundaries in the text
            sentence_endings = []
            
            # Pattern to match sentence endings
            sentence_pattern = r'[.!?]+(?:\s+|$)'
            matches = re.finditer(sentence_pattern, full_text)
            
            for match in matches:
                sentence_endings.append(match.end())
            
            if not sentence_endings:
                # If no sentence endings found, return all words as one group
                return self._smart_split_long_group(words, 8)  # Max 8 words
            
            # Map character positions to word indices
            word_groups = []
            current_char_pos = 0
            current_group = []
            word_index = 0
            
            for char_pos in sentence_endings:
                # Find words that belong to this sentence
                while word_index < len(words):
                    word = words[word_index]
                    
                    # Estimate character position for this word
                    word_end_pos = current_char_pos + len(word.word)
                    
                    current_group.append(word)
                    current_char_pos = word_end_pos + 1  # +1 for space
                    word_index += 1
                    
                    # If we've reached or passed the sentence ending
                    if current_char_pos >= char_pos:
                        break
                
                # Add this sentence group (with smart splitting if too long)
                if current_group:
                    # Check if sentence is too long and split it
                    if len(current_group) > 8:  # Max 8 words per slide
                        smart_groups = self._smart_split_long_group(current_group, 8)
                        word_groups.extend(smart_groups)
                    else:
                        word_groups.append(current_group.copy())
                    current_group = []
            
            # Add any remaining words
            if word_index < len(words):
                remaining_words = words[word_index:]
                if remaining_words:
                    if len(remaining_words) > 8:
                        smart_groups = self._smart_split_long_group(remaining_words, 8)
                        word_groups.extend(smart_groups)
                    else:
                        word_groups.append(remaining_words)
            
            # Filter out empty groups and ensure we don't lose any words
            word_groups = [group for group in word_groups if group]
            
            # If something went wrong, fallback to all words as one group
            if not word_groups:
                word_groups = self._smart_split_long_group(words, 8)
            
            logger.debug(f"Split {len(words)} words into {len(word_groups)} sentence groups (max 8 words each)")
            return word_groups
            
        except Exception as e:
            logger.error(f"Error splitting words by sentences: {str(e)}")
            # Fallback: smart split all words
            return self._smart_split_long_group(words, 8)
    
    def _smart_split_long_group(self, words: List[WordTiming], max_words: int) -> List[List[WordTiming]]:
        """Intelligently split long word groups at natural breakpoints"""
        try:
            if len(words) <= max_words:
                return [words]
            
            groups = []
            current_group = []
            
            # Natural breakpoint words (where it's good to split)
            break_words = {'and', 'but', 'or', 'so', 'yet', 'for', 'nor', 'because', 'since', 
                          'while', 'although', 'though', 'unless', 'until', 'when', 'where',
                          'if', 'that', 'which', 'who', 'what', 'how', 'then', 'now', 'here'}
            
            # Pause-indicating words (good places to break)
            pause_words = {'also', 'however', 'therefore', 'moreover', 'furthermore', 'meanwhile',
                          'consequently', 'nevertheless', 'nonetheless', 'otherwise', 'instead'}
            
            for i, word in enumerate(words):
                current_group.append(word)
                
                # Check if we should break here
                should_break = False
                
                # Break at max words
                if len(current_group) >= max_words:
                    should_break = True
                
                # Break at natural points before reaching max
                elif len(current_group) >= max_words - 2:  # 6+ words, look for break
                    word_text = word.word.lower().strip('.,!?;:')
                    
                    # Break after conjunctions and pause words
                    if word_text in break_words or word_text in pause_words:
                        should_break = True
                    
                    # Break after commas
                    elif word.word.endswith(','):
                        should_break = True
                    
                    # Break before "to" (infinitives)
                    elif i + 1 < len(words) and words[i + 1].word.lower() == 'to':
                        should_break = True
                
                # Create break
                if should_break and current_group:
                    groups.append(current_group.copy())
                    current_group = []
            
            # Add remaining words
            if current_group:
                groups.append(current_group)
            
            # If we still have groups that are too long, force split them
            final_groups = []
            for group in groups:
                if len(group) <= max_words:
                    final_groups.append(group)
                else:
                    # Force split into chunks
                    for i in range(0, len(group), max_words):
                        chunk = group[i:i + max_words]
                        if chunk:
                            final_groups.append(chunk)
            
            logger.debug(f"Smart split {len(words)} words into {len(final_groups)} groups")
            return final_groups
            
        except Exception as e:
            logger.error(f"Error in smart split: {str(e)}")
            # Fallback: simple chunking
            groups = []
            for i in range(0, len(words), max_words):
                chunk = words[i:i + max_words]
                if chunk:
                    groups.append(chunk)
            return groups
    
    def _create_word_group_clip(self, word_group: List[WordTiming], width: int, height: int,
                              font, highlight_color: str, duration: float, style: str) -> VideoClip:
        """Create a single sliding clip for a sentence group with minimal background"""
        try:
            from moviepy.editor import VideoClip
            
            # Create compact text images for each word state
            group_text = " ".join([w.word for w in word_group])
            
            # Calculate compact dimensions for sentence
            text_bbox = font.getbbox(group_text)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Handle long sentences - wrap if necessary
            max_width = int(width * 0.8)  # Use up to 80% of screen width
            if text_width > max_width:
                # For long sentences, allow wrapping
                wrapped_lines = self._wrap_sentence_to_lines(group_text, font, max_width)
                # Recalculate dimensions for wrapped text
                line_height = text_height
                text_height = line_height * len(wrapped_lines) + (4 * (len(wrapped_lines) - 1))  # 4px line spacing
                text_width = max_width
            
            # Minimal padding around text
            padding = 15
            img_width = min(text_width + (padding * 2), max_width + (padding * 2))
            img_height = text_height + (padding * 2)
            
            # Create images for each highlight state
            highlight_images = {}
            base_time = word_group[0].start
            
            # Create base image (no highlight)
            base_img = self._create_compact_text_image(
                group_text, img_width, img_height, font, None, -1, word_group
            )
            base_path = os.path.join(
                self.temp_dir, 
                f"sliding_sentence_{int(datetime.now().timestamp() * 1000000)}.png"
            )
            base_img.save(base_path, 'PNG')
            highlight_images[-1] = base_path
            
            # Create highlighted images for each word in sentence
            for i, word_timing in enumerate(word_group):
                highlighted_img = self._create_compact_text_image(
                    group_text, img_width, img_height, font, highlight_color, i, word_group
                )
                
                img_path = os.path.join(
                    self.temp_dir, 
                    f"sliding_sentence_word_{int(datetime.now().timestamp() * 1000000)}_{i}.png"
                )
                highlighted_img.save(img_path, 'PNG')
                highlight_images[i] = img_path
            
            def make_frame(t):
                """Generate frame with sentence-based sliding text highlighting"""
                try:
                    current_time = t + base_time
                    
                    # Find which word should be highlighted in this sentence
                    highlight_index = -1
                    for i, word_timing in enumerate(word_group):
                        if word_timing.start <= current_time <= word_timing.end + 0.1:  # Small buffer
                            highlight_index = i
                            break
                    
                    # Load appropriate image
                    img_path = highlight_images.get(highlight_index, highlight_images[-1])
                    img = Image.open(img_path)
                    
                    # Ensure RGB format
                    if img.mode != 'RGB':
                        rgb_img = Image.new('RGB', img.size, (0, 0, 0, 0))  # Transparent background
                        if img.mode == 'RGBA':
                            rgb_img.paste(img, mask=img.split()[-1])
                        else:
                            rgb_img.paste(img.convert('RGB'))
                        img = rgb_img
                    
                    return np.array(img)
                    
                except Exception as e:
                    logger.debug(f"Error in sentence make_frame at t={t}: {str(e)}")
                    # Return transparent frame as fallback
                    return np.zeros((img_height, img_width, 3), dtype=np.uint8)
            
            # Create the sliding sentence clip
            sentence_clip = VideoClip(make_frame, duration=duration)
            
            # Position at bottom center 
            y_position = height * 0.82  # Slightly higher for better visibility
            sentence_clip = sentence_clip.set_position(('center', y_position))
            
            # Add smooth fade effects for sentence transitions
            fade_duration = min(0.2, duration / 6)
            sentence_clip = sentence_clip.fadein(fade_duration).fadeout(fade_duration)
            
            logger.debug(f"Created sentence clip: {duration:.2f}s for '{group_text[:50]}...' ({len(word_group)} words)")
            return sentence_clip
                
        except Exception as e:
            logger.error(f"Error creating sentence group clip: {str(e)}")
            return None
    
    def _wrap_sentence_to_lines(self, sentence: str, font, max_width: int) -> List[str]:
        """Wrap a long sentence into multiple lines"""
        try:
            words = sentence.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                text_bbox = font.getbbox(test_line)
                text_width = text_bbox[2] - text_bbox[0]
                
                if text_width <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        # Word is too long for line, add it anyway
                        lines.append(word)
            
            if current_line:
                lines.append(' '.join(current_line))
            
            return lines
            
        except Exception as e:
            logger.error(f"Error wrapping sentence: {str(e)}")
            return [sentence]
    
    def _create_compact_text_image(self, text: str, img_width: int, img_height: int,
                                 font, highlight_color: str, highlight_index: int, 
                                 word_group: List[WordTiming]) -> Image.Image:
        """Create compact text image with minimal background and no black bars"""
        try:
            # Create transparent image (no black background!)
            img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            words = text.split()
            
            # Check if text needs wrapping
            text_bbox = font.getbbox(text)
            text_width = text_bbox[2] - text_bbox[0]
            max_width = img_width - 30  # Account for padding
            
            if text_width > max_width:
                # Handle multi-line text
                self._draw_wrapped_text_with_highlight(
                    draw, words, img_width, img_height, font, 
                    highlight_color, highlight_index
                )
            else:
                # Handle single-line text (original method)
                self._draw_single_line_text_with_highlight(
                    draw, words, img_width, img_height, font,
                    highlight_color, highlight_index
                )
            
            return img
            
        except Exception as e:
            logger.error(f"Error creating compact text image: {str(e)}")
            # Return minimal transparent image
            return Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
    
    def _draw_single_line_text_with_highlight(self, draw, words, img_width, img_height, 
                                            font, highlight_color, highlight_index):
        """Draw single line text with word highlighting"""
        # Calculate starting position for centered text
        full_text = " ".join(words)
        text_bbox = font.getbbox(full_text)
        text_width = text_bbox[2] - text_bbox[0]
        x_start = (img_width - text_width) // 2
        y_center = img_height // 2 - (text_bbox[3] - text_bbox[1]) // 2
        
        # Draw each word with proper spacing
        current_x = x_start
        
        for i, word in enumerate(words):
            is_highlighted = (i == highlight_index)
            
            if is_highlighted and highlight_color:
                # Highlighted word with glow effect
                self._draw_sliding_highlighted_word(
                    draw, (current_x, y_center), word, font, highlight_color
                )
            else:
                # Normal word with subtle outline
                normal_color = self._hex_to_rgba("#FFFFFF", 255)
                outline_color = self._hex_to_rgba("#000000", 120)
                
                # Subtle outline
                for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                    draw.text((current_x + dx, y_center + dy), word, 
                            font=font, fill=outline_color)
                
                # Main text
                draw.text((current_x, y_center), word, font=font, fill=normal_color)
            
            # Move to next word position
            word_width = font.getbbox(word + " ")[2] - font.getbbox(word + " ")[0]
            current_x += word_width
    
    def _draw_wrapped_text_with_highlight(self, draw, words, img_width, img_height,
                                        font, highlight_color, highlight_index):
        """Draw wrapped text with word highlighting across multiple lines"""
        max_width = img_width - 30  # Account for padding
        lines = []
        current_line = []
        
        # Break words into lines
        for word in words:
            test_line = ' '.join(current_line + [word])
            text_bbox = font.getbbox(test_line)
            text_width = text_bbox[2] - text_bbox[0]
            
            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(current_line)
                    current_line = [word]
                else:
                    # Word is too long, add it anyway
                    lines.append([word])
        
        if current_line:
            lines.append(current_line)
        
        # Calculate line height and starting position
        line_height = font.getbbox('Ag')[3] - font.getbbox('Ag')[1]
        total_height = line_height * len(lines) + (4 * (len(lines) - 1))  # 4px line spacing
        y_start = (img_height - total_height) // 2
        
        # Draw each line
        word_index = 0
        for line_num, line_words in enumerate(lines):
            line_text = " ".join(line_words)
            text_bbox = font.getbbox(line_text)
            text_width = text_bbox[2] - text_bbox[0]
            x_start = (img_width - text_width) // 2
            y_pos = y_start + (line_num * (line_height + 4))
            
            # Draw words in this line
            current_x = x_start
            for word in line_words:
                is_highlighted = (word_index == highlight_index)
                
                if is_highlighted and highlight_color:
                    # Highlighted word
                    self._draw_sliding_highlighted_word(
                        draw, (current_x, y_pos), word, font, highlight_color
                    )
                else:
                    # Normal word
                    normal_color = self._hex_to_rgba("#FFFFFF", 255)
                    outline_color = self._hex_to_rgba("#000000", 120)
                    
                    # Subtle outline
                    for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                        draw.text((current_x + dx, y_pos + dy), word,
                                font=font, fill=outline_color)
                    
                    # Main text
                    draw.text((current_x, y_pos), word, font=font, fill=normal_color)
                
                # Move to next word position
                word_width = font.getbbox(word + " ")[2] - font.getbbox(word + " ")[0]
                current_x += word_width
                word_index += 1
    
    def _draw_sliding_highlighted_word(self, draw: ImageDraw.Draw, position: tuple, 
                                     word: str, font, highlight_color: str):
        """Draw highlighted word with subtle glow for sliding effect"""
        x, y = position
        
        try:
            main_color = self._hex_to_rgba(highlight_color, 255)
            glow_color = self._hex_to_rgba(highlight_color, 80)
            
            # Subtle glow effect (smaller than before)
            for radius in range(2, 0, -1):
                alpha = 40 + (radius * 20)
                glow = self._hex_to_rgba(highlight_color, alpha)
                
                for dx in range(-radius, radius + 1):
                    for dy in range(-radius, radius + 1):
                        if dx*dx + dy*dy <= radius*radius:
                            draw.text((x + dx, y + dy), word, font=font, fill=glow)
            
            # Bold effect with smaller offset
            for bold_offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                draw.text((x + bold_offset[0], y + bold_offset[1]), word, 
                        font=font, fill=main_color)
            
            # Main highlighted text
            draw.text((x, y), word, font=font, fill=main_color)
            
        except Exception as e:
            logger.debug(f"Error drawing sliding highlighted word: {str(e)}")
            # Fallback to simple highlight
            main_color = self._hex_to_rgba(highlight_color, 255)
            draw.text((x, y), word, font=font, fill=main_color)
    
    def _create_karaoke_segment_clip(self, segment: KaraokeSegment, width: int, height: int,
                                   colors: Dict[str, str], style: str) -> VideoClip:
        """Create a single karaoke segment with word-by-word highlighting - NO duplicate subtitles"""
        try:
            segment_duration = segment.end_time - segment.start_time
            
            # Create a single text clip that changes highlighting over time
            # Instead of layering base text + highlights, create one dynamic text clip
            
            # FIXED: Better responsive font sizing
            if width >= 1920:  # 4K/Full HD
                font_size = 36
            elif width >= 1280:  # HD
                font_size = 28
            elif width >= 854:   # SD
                font_size = 24
            else:  # Very small
                font_size = 20
            
            font = self._load_font(font_size)
            
            # Create single karaoke text clip with time-based highlighting
            karaoke_clip = self._create_dynamic_karaoke_clip(
                segment, width, height, colors, style, font, segment_duration
            )
            
            return karaoke_clip
                
        except Exception as e:
            logger.error(f"Error creating karaoke segment clip: {str(e)}")
            return None
    
    def _create_dynamic_karaoke_clip(self, segment: KaraokeSegment, width: int, height: int,
                                   colors: Dict[str, str], style: str, font, duration: float) -> VideoClip:
        """Create a single smooth karaoke clip with time-based word highlighting (NO FLICKERING)"""
        try:
            # Get highlight color
            highlight_color = self.highlight_colors.get(style, self.highlight_colors["default"])
            
            # Create all possible text images upfront (one for each word highlighted)
            text_images = {}
            
            # Create base image (no words highlighted)
            base_img = self._create_text_image_no_highlight(segment.full_text, width, height, font)
            
            # FIXED: Ensure RGB format for MoviePy compatibility
            if base_img.mode != 'RGB':
                rgb_img = Image.new('RGB', base_img.size, (0, 0, 0))
                rgb_img.paste(base_img, mask=base_img.split()[-1] if base_img.mode == 'RGBA' else None)
                base_img = rgb_img
            
            base_path = os.path.join(
                self.temp_dir, 
                f"karaoke_base_{int(datetime.now().timestamp() * 1000000)}.png"
            )
            base_img.save(base_path, 'PNG')
            text_images[-1] = base_path  # -1 = no highlight
            
            # Create image for each word highlighted
            for i, word_timing in enumerate(segment.words):
                highlighted_img = self._create_text_image_with_highlight(
                    segment.full_text, word_timing.word, i, segment.words,
                    width, height, font, highlight_color
                )
                
                # FIXED: Ensure RGB format for MoviePy compatibility
                if highlighted_img.mode != 'RGB':
                    rgb_img = Image.new('RGB', highlighted_img.size, (0, 0, 0))
                    rgb_img.paste(highlighted_img, mask=highlighted_img.split()[-1] if highlighted_img.mode == 'RGBA' else None)
                    highlighted_img = rgb_img
                
                img_path = os.path.join(
                    self.temp_dir, 
                    f"karaoke_word_{int(datetime.now().timestamp() * 1000000)}_{i}.png"
                )
                highlighted_img.save(img_path, 'PNG')
                text_images[i] = img_path
            
            # Create a function that determines which image to show at any given time
            def get_image_at_time(t):
                """Return the appropriate image path for time t"""
                current_time = t  # t is relative to segment start
                
                # Find which word should be highlighted at this time
                for i, word_timing in enumerate(segment.words):
                    word_start = word_timing.start - segment.start_time
                    word_end = word_timing.end - segment.start_time
                    
                    # Use slightly overlapping timing to prevent gaps
                    if word_start <= current_time <= word_end + 0.01:  # Small overlap
                        return text_images[i]  # Highlight this word
                
                # Check if we're very close to a word (within 50ms) to handle timing precision issues
                for i, word_timing in enumerate(segment.words):
                    word_start = word_timing.start - segment.start_time
                    word_end = word_timing.end - segment.start_time
                    
                    if abs(current_time - word_start) <= 0.05 or abs(current_time - word_end) <= 0.05:
                        return text_images[i]  # Show highlight if very close
                
                # No word is being spoken, show base text
                return text_images[-1]
            
            # FIXED: Create a single ImageClip that changes over time with proper RGB format
            def make_frame(t):
                """Generate frame for time t with verified RGB format"""
                try:
                    img_path = get_image_at_time(t)
                    # Load and ensure RGB format
                    img = Image.open(img_path)
                    
                    # FIXED: Force RGB conversion with proper transparency handling
                    if img.mode != 'RGB':
                        rgb_img = Image.new('RGB', img.size, (0, 0, 0))
                        if img.mode == 'RGBA':
                            # Composite RGBA onto black background
                            rgb_img.paste(img, mask=img.split()[-1])
                        else:
                            # Convert other modes to RGB
                            rgb_img.paste(img.convert('RGB'))
                        img = rgb_img
                    
                    # Convert to numpy array with explicit RGB format verification
                    frame = np.array(img)
                    
                    # FIXED: Verify frame shape before returning
                    if len(frame.shape) != 3 or frame.shape[2] != 3:
                        logger.warning(f"Invalid frame shape {frame.shape}, creating fallback RGB frame")
                        # Create fallback RGB frame
                        fallback_img = Image.new('RGB', img.size, (0, 0, 0))
                        frame = np.array(fallback_img)
                    
                    return frame
                    
                except Exception as e:
                    logger.debug(f"Error in make_frame at t={t}: {str(e)}")
                    # Return base image as fallback with proper RGB handling
                    try:
                        img = Image.open(text_images[-1])
                        if img.mode != 'RGB':
                            rgb_img = Image.new('RGB', img.size, (0, 0, 0))
                            if img.mode == 'RGBA':
                                rgb_img.paste(img, mask=img.split()[-1])
                            else:
                                rgb_img.paste(img.convert('RGB'))
                            img = rgb_img
                        return np.array(img)
                    except:
                        # Last resort: return a black frame
                        return np.zeros((height, width, 3), dtype=np.uint8)
            
            # Create the dynamic clip
            from moviepy.editor import VideoClip
            
            # Get image dimensions
            sample_img = Image.open(text_images[-1])
            img_width, img_height = sample_img.size
            
            dynamic_clip = VideoClip(make_frame, duration=duration)
            # FIXED: Position higher to prevent bottom cutoff  
            dynamic_clip = dynamic_clip.set_position(('center', height * 0.75))
            
            # IMPROVED: Smoother fade effects
            fade_duration = min(0.15, duration / 5)
            dynamic_clip = dynamic_clip.fadein(fade_duration).fadeout(fade_duration)
            
            logger.debug(f"Created smooth karaoke clip: {duration:.2f}s with {len(segment.words)} words")
            return dynamic_clip
                
        except Exception as e:
            logger.error(f"Error creating smooth karaoke clip: {str(e)}")
            return self._create_static_text_clip(segment.full_text, width, height, font, duration)
    
    def _create_text_image_with_highlight(self, full_text: str, highlighted_word: str, 
                                        word_index: int, all_words: list, width: int, height: int,
                                        font, highlight_color: str) -> Image.Image:
        """Create image with one word dynamically animated (bold, glow, color pop)"""
        try:
            # IMPROVED: Larger canvas to prevent cropping
            img_width = int(width * 0.95)  # Wider canvas
            img_height = int(height * 0.3)  # Taller canvas
            
            img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # IMPROVED: Better text wrapping with more space
            wrapped_text = self._wrap_text(full_text, font, img_width - 60)
            
            # Calculate text position
            bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, spacing=4)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (img_width - text_width) // 2
            y = (img_height - text_height) // 2
            
            # IMPROVED: More subtle background styling
            padding = 15
            bg_coords = [
                x - padding, y - padding,
                x + text_width + padding, y + text_height + padding
            ]
            draw.rounded_rectangle(bg_coords, radius=8, fill=(0, 0, 0, 140))
            
            # ENHANCED: Dynamic word-by-word animation effects
            words = full_text.split()
            current_x = x
            current_y = y
            
            for i, word in enumerate(words):
                # Check if this is the highlighted word
                is_highlighted = (i == word_index)
                
                if is_highlighted:
                    # 🎬 ANIMATED HIGHLIGHTED WORD with multiple effects
                    self._draw_animated_word(draw, (current_x, current_y), word, font, 
                                           highlight_color, img_width, img_height)
                else:
                    # Normal word styling
                    color = self._hex_to_rgba(self.text_colors["default"], 255)
                    self._draw_text_with_outline(
                        draw, (current_x, current_y), word, font, color, 
                        self._hex_to_rgba(self.text_colors["shadow"], 180)
                    )
                
                # Move to next word position
                word_width = font.getbbox(word + " ")[2] - font.getbbox(word + " ")[0]
                current_x += word_width
                
                # Handle line wrapping (simplified) - using updated canvas margin
                if current_x > img_width - 60:
                    current_x = x
                    current_y += font.getbbox('Ag')[3] - font.getbbox('Ag')[1] + 8
            
            return img
            
        except Exception as e:
            logger.error(f"Error creating highlighted text image: {str(e)}")
            return self._create_text_image_no_highlight(full_text, width, height, font)
    
    def _draw_animated_word(self, draw: ImageDraw.Draw, position: tuple, word: str, 
                          font, highlight_color: str, canvas_width: int, canvas_height: int):
        """Draw word with MULTIPLE ANIMATION EFFECTS: glow, bold, color pop, scale"""
        x, y = position
        
        try:
            # 🌟 EFFECT 1: GLOW EFFECT (multiple colored outlines)
            glow_color = self._hex_to_rgba(highlight_color, 100)
            for radius in range(4, 0, -1):  # Create glow fade
                alpha = 50 + (radius * 15)  # Fade out glow
                glow = self._hex_to_rgba(highlight_color, alpha)
                
                # Draw glow outline
                for dx in range(-radius, radius + 1):
                    for dy in range(-radius, radius + 1):
                        if dx*dx + dy*dy <= radius*radius:
                            draw.text((x + dx, y + dy), word, font=font, fill=glow)
            
            # 🎯 EFFECT 2: BOLD EFFECT (multiple text overlays for thickness)
            main_color = self._hex_to_rgba(highlight_color, 255)
            
            # Draw bold by layering text slightly offset
            for bold_offset in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
                draw.text((x + bold_offset[0], y + bold_offset[1]), word, font=font, fill=main_color)
            
            # 🔥 EFFECT 3: COLOR POP with contrasting outline
            pop_color = self._get_contrasting_color(highlight_color)
            contrast_outline = self._hex_to_rgba(pop_color, 200)
            
            # Strong contrast outline
            for outline_offset in [(-2, -2), (-2, 0), (-2, 2), (0, -2), (0, 2), (2, -2), (2, 0), (2, 2)]:
                draw.text((x + outline_offset[0], y + outline_offset[1]), word, font=font, fill=contrast_outline)
            
            # ✨ EFFECT 4: SCALED/EMPHASIZED main text 
            # Use a larger font for the highlighted word if possible
            try:
                from PIL import ImageFont
                scaled_font_size = int(font.size * 1.2)  # 20% larger
                scaled_font = self._load_font(scaled_font_size)
                
                # Adjust position for larger text
                bbox = scaled_font.getbbox(word)
                scaled_width = bbox[2] - bbox[0]
                scaled_height = bbox[3] - bbox[1]
                
                # Center the scaled text
                scaled_x = x - ((scaled_width - font.getbbox(word)[2]) // 2)
                scaled_y = y - ((scaled_height - font.getbbox(word)[3]) // 2)
                
                # Draw the main highlighted word with scaled font
                draw.text((scaled_x, scaled_y), word, font=scaled_font, fill=main_color)
                
            except:
                # Fallback: draw with original font
                draw.text((x, y), word, font=font, fill=main_color)
            
            # 💫 EFFECT 5: SPARKLE/HIGHLIGHT background
            word_bbox = font.getbbox(word)
            word_width = word_bbox[2] - word_bbox[0]
            word_height = word_bbox[3] - word_bbox[1]
            
            # Create animated highlight background
            highlight_coords = [
                x - 8, y - 6,
                x + word_width + 8, y + word_height + 6
            ]
            
            # Gradient-like highlight background
            highlight_bg = self._hex_to_rgba(highlight_color, 60)
            draw.rounded_rectangle(highlight_coords, radius=6, fill=highlight_bg)
            
            # Add small accent marks for extra pop
            accent_color = self._hex_to_rgba(highlight_color, 180)
            
            # Small decorative elements around the word
            draw.ellipse([x - 4, y + word_height//2 - 2, x - 1, y + word_height//2 + 1], fill=accent_color)
            draw.ellipse([x + word_width + 1, y + word_height//2 - 2, x + word_width + 4, y + word_height//2 + 1], fill=accent_color)
            
        except Exception as e:
            logger.debug(f"Error in animated word drawing: {str(e)}")
            # Fallback to simple highlight
            main_color = self._hex_to_rgba(highlight_color, 255)
            draw.text((x, y), word, font=font, fill=main_color)

    def _get_contrasting_color(self, hex_color: str) -> str:
        """Get a contrasting color for better visual pop"""
        try:
            # Remove # if present
            hex_color = hex_color.lstrip('#')
            
            # Convert to RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            # Calculate luminance
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            
            # Return contrasting color
            if luminance > 0.5:
                return "#000000"  # Dark for light colors
            else:
                return "#FFFFFF"  # Light for dark colors
                
        except:
            return "#FFFFFF"  # Default contrast
    
    def _create_text_image_no_highlight(self, text: str, width: int, height: int, font) -> Image.Image:
        """Create image with plain text (no highlighting)"""
        try:
            # IMPROVED: Larger canvas to prevent cropping (matching highlight method)
            img_width = int(width * 0.95)  # Wider canvas
            img_height = int(height * 0.3)  # Taller canvas
            
            img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # IMPROVED: Better text wrapping with more space
            wrapped_text = self._wrap_text(text, font, img_width - 60)
            
            # Calculate text position
            bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, spacing=4)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (img_width - text_width) // 2
            y = (img_height - text_height) // 2
            
            # IMPROVED: More subtle background styling (matching highlight method)
            padding = 15
            bg_coords = [
                x - padding, y - padding,
                x + text_width + padding, y + text_height + padding
            ]
            draw.rounded_rectangle(bg_coords, radius=8, fill=(0, 0, 0, 140))
            
            # Draw text with outline
            self._draw_text_with_outline(
                draw, (x, y), wrapped_text, font,
                text_color=self.text_colors["default"],
                outline_color=self.text_colors["shadow"]
            )
            
            return img
            
        except Exception as e:
            logger.error(f"Error creating plain text image: {str(e)}")
            # Return blank transparent image with updated canvas size
            return Image.new('RGBA', (int(width * 0.95), int(height * 0.3)), (0, 0, 0, 0))
    
    def _create_static_text_clip(self, text: str, width: int, height: int, font, duration: float):
        """Create fallback static text clip"""
        try:
            img = self._create_text_image_no_highlight(text, width, height, font)
            
            temp_path = os.path.join(
                self.temp_dir, 
                f"static_text_{int(datetime.now().timestamp() * 1000000)}.png"
            )
            img.save(temp_path, 'PNG')
            
            from moviepy.editor import ImageClip
            clip = ImageClip(temp_path, duration=duration)
            # FIXED: Position higher to prevent bottom cutoff (consistent with other clips)
            clip = clip.set_position(('center', height * 0.75))
            
            return clip
            
        except Exception as e:
            logger.error(f"Error creating static text clip: {str(e)}")
            from moviepy.editor import ColorClip
            return ColorClip(size=(width, height), color=(0,0,0), duration=duration).set_opacity(0)
    
    def _load_font(self, font_size: int) -> ImageFont.FreeTypeFont:
        """Load the best available font"""
        font_paths = [
            "/System/Library/Fonts/Arial.ttf",  # macOS
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
            "C:/Windows/Fonts/arial.ttf",  # Windows
        ]
        
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, font_size)
            except:
                continue
        
        return ImageFont.load_default()
    
    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> str:
        """Wrap text to fit within specified width"""
        try:
            words = text.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = font.getbbox(test_line)
                text_width = bbox[2] - bbox[0]
                
                if text_width <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        lines.append(word)
            
            if current_line:
                lines.append(' '.join(current_line))
            
            return '\n'.join(lines)
            
        except Exception as e:
            logger.warning(f"Error wrapping text: {str(e)}")
            return text
    
    def _draw_text_with_outline(self, draw: ImageDraw.Draw, position: tuple,
                              text: str, font: ImageFont.FreeTypeFont,
                              text_color = "#FFFFFF", outline_color = "#000000"):
        """Draw text with subtle outline for better visibility"""
        x, y = position
        
        # Convert colors to RGBA tuples if they're strings
        if isinstance(text_color, str):
            text_color = self._hex_to_rgba(text_color, 255)
        if isinstance(outline_color, str):
            outline_color = self._hex_to_rgba(outline_color, 180)  # More transparent outline
        
        # IMPROVED: Thinner, more subtle outline (only 1px instead of 2px)
        draw.text((x-1, y-1), text, font=font, fill=outline_color)
        draw.text((x+1, y-1), text, font=font, fill=outline_color)
        draw.text((x-1, y+1), text, font=font, fill=outline_color)
        draw.text((x+1, y+1), text, font=font, fill=outline_color)
        
        # Draw main text
        draw.text((x, y), text, font=font, fill=text_color)
    
    def _hex_to_rgba(self, hex_color: str, alpha: int = 255) -> tuple:
        """Convert hex color to RGBA tuple"""
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return (r, g, b, alpha)
        except:
            return (255, 255, 255, alpha)  # Default to white
    
    def create_karaoke_preview(self, segments: List[KaraokeSegment], 
                             session_id: str) -> str:
        """Create a text preview of the karaoke timing for debugging"""
        try:
            preview_path = os.path.join(self.temp_dir, f"{session_id}_karaoke_preview.txt")
            
            with open(preview_path, 'w', encoding='utf-8') as f:
                f.write("=== KARAOKE SUBTITLE PREVIEW ===\n\n")
                
                for segment in segments:
                    f.write(f"Segment {segment.segment_id + 1} ({segment.start_time:.2f}s - {segment.end_time:.2f}s):\n")
                    f.write(f"Full text: {segment.full_text}\n")
                    f.write("Word timing:\n")
                    
                    for word in segment.words:
                        f.write(f"  '{word.word}' @ {word.start:.2f}s - {word.end:.2f}s (conf: {word.confidence:.2f})\n")
                    
                    f.write("\n" + "="*50 + "\n\n")
                
                # Add timing statistics
                all_words = [w for s in segments for w in s.words]
                if all_words:
                    total_duration = max(w.end for w in all_words)
                    wpm = len(all_words) / (total_duration / 60)
                    avg_confidence = sum(w.confidence for w in all_words) / len(all_words)
                    
                    f.write("STATISTICS:\n")
                    f.write(f"Total words: {len(all_words)}\n")
                    f.write(f"Total duration: {total_duration:.2f}s\n")
                    f.write(f"Words per minute: {wpm:.1f}\n")
                    f.write(f"Average confidence: {avg_confidence:.2f}\n")
            
            logger.info(f"Karaoke preview saved to: {preview_path}")
            return preview_path
            
        except Exception as e:
            logger.error(f"Error creating karaoke preview: {str(e)}")
            return "" 
    
    def cleanup_temp_files(self, max_age_minutes: int = 30):
        """Clean up temporary karaoke image files"""
        try:
            import glob
            import time
            
            logger.debug("Cleaning up karaoke temporary files")
            
            current_time = time.time()
            cutoff_time = current_time - (max_age_minutes * 60)
            removed_count = 0
            
            # Karaoke-specific temporary file patterns
            karaoke_patterns = [
                "karaoke_base_*.png",
                "karaoke_word_*.png",
                "sliding_base_*.png", 
                "sliding_word_*.png",
                "sliding_sentence_*.png",
                "sliding_sentence_word_*.png",
                "static_text_*.png"
            ]
            
            for pattern in karaoke_patterns:
                files = glob.glob(os.path.join(self.temp_dir, pattern))
                for file_path in files:
                    try:
                        if os.path.isfile(file_path):
                            file_mtime = os.path.getmtime(file_path)
                            # Remove files older than cutoff time
                            if file_mtime < cutoff_time:
                                os.remove(file_path)
                                removed_count += 1
                                logger.debug(f"Removed karaoke temp file: {os.path.basename(file_path)}")
                    except Exception as e:
                        logger.debug(f"Could not remove karaoke temp file {file_path}: {str(e)}")
            
            if removed_count > 0:
                logger.debug(f"Removed {removed_count} karaoke temp files")
            
        except Exception as e:
            logger.debug(f"Error cleaning up karaoke temp files: {str(e)}")
    
    def force_cleanup_all_temp_files(self):
        """Force cleanup of all karaoke temp files regardless of age"""
        try:
            import glob
            
            logger.info("Force cleaning all karaoke temporary files")
            removed_count = 0
            
            # All karaoke temporary file patterns
            karaoke_patterns = [
                "karaoke_*.png",
                "sliding_*.png", 
                "static_text_*.png"
            ]
            
            for pattern in karaoke_patterns:
                files = glob.glob(os.path.join(self.temp_dir, pattern))
                for file_path in files:
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            removed_count += 1
                            logger.debug(f"Force removed: {os.path.basename(file_path)}")
                    except Exception as e:
                        logger.debug(f"Could not remove {file_path}: {str(e)}")
            
            logger.info(f"Force removed {removed_count} karaoke temp files")
            
        except Exception as e:
            logger.error(f"Error in force cleanup: {str(e)}") 