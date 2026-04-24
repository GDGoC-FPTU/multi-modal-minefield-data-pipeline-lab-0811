import re

# ==========================================
# ROLE 2: ETL/ELT BUILDER
# ==========================================
# Task: Clean the transcript text and extract key information.

def clean_transcript(file_path):
    # --- FILE READING (Handled for students) ---
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    # ------------------------------------------
    
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
        "hai trăm nghìn": 200000
    }
    
    extracted_price = 0
    for phrase, value in vn_number_map.items():
        if phrase in cleaned_text.lower():
            extracted_price = value
            break
            
    # Also look for digits if words fail
    if extracted_price == 0:
        digit_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*VND', cleaned_text)
        if digit_match:
            extracted_price = float(digit_match.group(1).replace(',', ''))

    # Final cleanup of extra whitespace and speaker labels
    cleaned_text = re.sub(r'\[Speaker \d\]:', '', cleaned_text)
    cleaned_text = re.sub(r'\n+', '\n', cleaned_text).strip()

    return {
        "document_id": "transcript-001",
        "content": cleaned_text,
        "source_type": "Video",
        "author": "Speaker 1",
        "timestamp": None,
        "source_metadata": {
            "detected_price_vnd": extracted_price,
            "has_noise_removed": True
        }
    }

