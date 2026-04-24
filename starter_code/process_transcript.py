"""Transcript Processing Module: Clean and extract data from video transcripts.

Processes transcribed video content to:
- Remove timestamps and noise markers
- Extract price mentions (Vietnamese word-based pricing)
- Clean speaker labels and formatting
- Normalize content for the knowledge base

Author: ETL/ELT Builder (Role 2)
"""

import re
import logging
import os

logger = logging.getLogger(__name__)

# ==========================================
# ROLE 2: ETL/ELT BUILDER
# ==========================================
# Task: Clean the transcript text and extract key information.

def clean_transcript(file_path):
    """Clean video transcript and extract structured information.
    
    Removes:
    - Timestamps: [00:05:12] → removed
    - Noise markers: [Music], [Laughter], [inaudible] → removed
    - Speaker labels: [Speaker 1]: → removed
    
    Extracts:
    - Prices mentioned in Vietnamese (\"năm trăm nghìn\" = 500,000 VND)
    - Numeric prices with VND suffix
    
    Args:
        file_path (str): Path to text file with transcript
        
    Returns:
        dict: UnifiedDocument-compatible dict with cleaned content and extracted metadata.
              Returns dict with empty content if file missing/unreadable.
              
    Raises:
        Exception: Caught and logged; returns fallback dict instead of crashing
    """
    # Validate file
    if not os.path.exists(file_path):
        logger.error(f"Transcript file not found: {file_path}")
        return {
            "document_id": "transcript-000",
            "content": "ERROR: Transcript file not found",
            "source_type": "Video",
            "author": "Unknown",
            "source_metadata": {"detected_price_vnd": 0, "has_noise_removed": False, "error": True}
        }
    
    if not file_path.lower().endswith(('.txt', '.text')):
        logger.warning(f"File {file_path} is not a .txt file. Attempting to read anyway.")
    
    # Read file with error handling
    logger.info(f"Reading transcript file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        if not text or not text.strip():
            logger.warning("Transcript file is empty")
            text = "(empty transcript)"
    except UnicodeDecodeError:
        logger.warning(f"UTF-8 decode error, trying latin-1 encoding")
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                text = f.read()
        except Exception as e:
            logger.error(f"Failed to read transcript file: {e}")
            return {
                "document_id": "transcript-000",
                "content": f"ERROR: Failed to read file ({str(e)})",
                "source_type": "Video",
                "author": "Unknown",
                "source_metadata": {"detected_price_vnd": 0, "has_noise_removed": False, "error": True}
            }
    except Exception as e:
        logger.error(f"Failed to read transcript file: {e}")
        return {
            "document_id": "transcript-000",
            "content": f"ERROR: Failed to read file",
            "source_type": "Video",
            "author": "Unknown",
            "source_metadata": {"detected_price_vnd": 0, "has_noise_removed": False, "error": True}
        }
    
    # 1. Remove noise tokens like [Music], [inaudible], [Laughter]
    # This also handles [Music starts], [Speaker 1]: etc.
    cleaned_text = re.sub(r'\[Music.*?\]', '', text)
    cleaned_text = re.sub(r'\[inaudible\]', '', cleaned_text)
    cleaned_text = re.sub(r'\[Laughter\]', '', cleaned_text)
    
    # 2. Strip timestamps [00:00:00]
    cleaned_text = re.sub(r'\[\d{2}:\d{2}:\d{2}\]', '', cleaned_text)
    
    # 3. Find the price mentioned in Vietnamese words ("năm trăm nghìn")
    # Mapping for Vietnamese numbers
    vn_number_map = {
        "năm trăm nghìn": 500000,
        "một triệu": 1000000,
        "hai trăm nghìn": 200000,
        "năm mươi nghìn": 50000,
        "mười nghìn": 10000
    }
    
    extracted_price = 0
    price_source = "none"
    
    # Look for Vietnamese number words (case-insensitive)
    for phrase, value in vn_number_map.items():
        if phrase in cleaned_text.lower():
            extracted_price = value
            price_source = f"vietnamese_words({phrase})"
            logger.info(f"Detected Vietnamese price: {phrase} → {value} VND")
            break
    
    # Also look for digits if words fail
    if extracted_price == 0:
        digit_match = re.search(r'(\d{1,3}(?:,\d{3})*\s*(?:VND)?)', cleaned_text, re.IGNORECASE)
        if digit_match:
            try:
                extracted_price = float(digit_match.group(1).replace(',', '').replace('vnd', '').strip())
                price_source = f"digit_pattern"
                if extracted_price > 0:
                    logger.info(f"Detected numeric price: {extracted_price} VND")
            except ValueError:
                logger.debug(f"Could not parse extracted price digits: {digit_match.group(1)}")
                extracted_price = 0

    # Final cleanup of extra whitespace and speaker labels
    cleaned_text = re.sub(r'\[Speaker \d\]:', '', cleaned_text)
    cleaned_text = re.sub(r'\n+', '\n', cleaned_text).strip()
    
    # Validate cleaned content has minimum length
    if len(cleaned_text) < 20:
        logger.warning(f"Transcript cleaned content is very short ({len(cleaned_text)} chars)")
    
    logger.info(f"Transcript cleaned: {len(text)} → {len(cleaned_text)} chars. Price extracted: {extracted_price} VND")

    return {
        "document_id": "transcript-001",
        "content": cleaned_text,
        "source_type": "Video",
        "author": "Speaker 1",
        "timestamp": None,
        "source_metadata": {
            "detected_price_vnd": float(extracted_price),
            "price_extraction_method": price_source,
            "has_noise_removed": True,
            "original_length": len(text),
            "cleaned_length": len(cleaned_text)
        }
    }

