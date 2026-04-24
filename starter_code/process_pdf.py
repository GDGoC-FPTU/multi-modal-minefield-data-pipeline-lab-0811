"""PDF Processing Module: Extract structured data from PDF documents using Gemini API.

Handles PDF files containing lecture notes, technical documentation, or structured content.
Leverages Google's Gemini vision model to extract text, summaries, and metadata.

Author: ETL/ELT Builder (Role 2)
"""

import google.generativeai as genai
import os
import json
import time
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    logger.warning("GEMINI_API_KEY not found in .env. PDF extraction will fail.")
else:
    genai.configure(api_key=api_key)

def extract_pdf_data(file_path):
    """Extract structured data from a PDF file using Gemini API.
    
    Args:
        file_path (str): Path to the PDF file to process
        
    Returns:
        dict: UnifiedDocument-compliant dictionary with extracted data:
            - document_id: pdf-{filename}
            - content: 3+ sentence summary + topics
            - source_type: 'PDF'
            - author: Detected author from document
            - source_metadata: tables_found flag, original filename
            
    Returns None if:
        - File doesn't exist
        - Gemini API key is missing
        - Upload or API call fails after retries
        - Response JSON is invalid
        
    Raises:
        Exception: Caught and logged; returns None instead of crashing
    """
    # Validate file existence and is a PDF
    if not os.path.exists(file_path):
        logger.error(f"PDF file not found: {file_path}")
        return None
    
    if not file_path.lower().endswith('.pdf'):
        logger.warning(f"File {file_path} is not a PDF. Attempting to process anyway.")
    
    # Check file size (warn if too large for API)
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > 20:
        logger.warning(f"PDF file is large ({file_size_mb:.1f}MB). Processing may take longer.")
    
    logger.info(f"Starting PDF extraction: {file_path}")
        
    # Model selection with fallback
    model = None
    for model_name in ['gemini-1.5-flash', 'gemini-pro', 'gemini-1.5-pro']:
        try:
            model = genai.GenerativeModel(model_name)
            logger.info(f"Using model: {model_name}")
            break
        except Exception as e:
            logger.debug(f"Model {model_name} not available: {e}")
            continue
    
    if model is None:
        logger.error("No valid Gemini model available for PDF extraction")
        return None
    
    # Upload file with validation
    logger.info(f"Uploading PDF to Gemini: {os.path.basename(file_path)}")
    max_upload_retries = 3
    pdf_file = None
    
    for attempt in range(max_upload_retries):
        try:
            pdf_file = genai.upload_file(path=file_path)
            logger.debug(f"File uploaded successfully: {pdf_file.name}")
            break
        except Exception as e:
            logger.warning(f"Upload attempt {attempt + 1}/{max_upload_retries} failed: {e}")
            if attempt < max_upload_retries - 1:
                time.sleep(1)
            else:
                logger.error(f"Failed to upload PDF after {max_upload_retries} attempts")
                return None
    
    # Wait for file processing with timeout
    processing_timeout = 60  # seconds
    start_wait = time.time()
    while pdf_file.state.name == "PROCESSING":
        elapsed = time.time() - start_wait
        if elapsed > processing_timeout:
            logger.error(f"PDF processing timeout after {processing_timeout}s")
            return None
        logger.debug(f"Waiting for file processing... ({elapsed:.1f}s elapsed)")
        time.sleep(2)
        pdf_file = genai.get_file(pdf_file.name)
        
    prompt = """
Analyze this document and extract a summary and the author. 
Output exactly as a JSON object matching this exact format:
{
    "document_id": "pdf-doc-001",
    "content": "Summary: [Insert your 3-sentence summary here]. Topics: [List main topics]",
    "source_type": "PDF",
    "author": "[Insert author name here]",
    "timestamp": null,
    "source_metadata": {
        "original_file": "lecture_notes.pdf",
        "tables_found": true/false
    }
}
"""
    
    logger.info("Generating content from PDF using Gemini...")
    
    # Exponential Backoff for rate limiting (429 errors)
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content([pdf_file, prompt])
            content_text = response.text
            
            if not content_text or not content_text.strip():
                logger.warning("Gemini returned empty response")
                return None
            
            # Parse JSON from response (handle markdown code blocks)
            if "```json" in content_text:
                content_text = content_text.split("```json")[1].split("```")[0]
            elif "```" in content_text:
                content_text = content_text.split("```")[1].split("```")[0]
            
            # Validate JSON structure
            extracted_data = json.loads(content_text.strip())
            
            # Verify required fields are present
            required_fields = ['document_id', 'content', 'source_type']
            for field in required_fields:
                if field not in extracted_data:
                    logger.warning(f"Extracted data missing required field: {field}")
                    extracted_data[field] = extracted_data.get(field, "Unknown")
            
            logger.info(f"Successfully extracted PDF: {extracted_data.get('document_id', 'unknown')}")
            return extracted_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini response: {e}")
            logger.debug(f"Raw response: {content_text[:200]}...")
            return None
        except Exception as e:
            error_str = str(e).lower()
            if "429" in str(e) or "quota" in error_str or "rate" in error_str:
                logger.warning(f"Rate limit hit (429). Attempt {attempt + 1}/{max_retries}. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.error(f"Error generating content (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    logger.error("All PDF extraction retries exhausted")
                    break
                time.sleep(1)
    
    logger.error("Failed to extract PDF data after all retries")
    return None
