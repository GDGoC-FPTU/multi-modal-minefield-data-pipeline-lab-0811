import google.generativeai as genai
import os
import json
import time
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def extract_pdf_data(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return None
        
    # Using gemini-1.5-flash which is standard. If not found, fallback to gemini-pro.
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception:
        model = genai.GenerativeModel('gemini-pro')
    
    print(f"Uploading {file_path} to Gemini...")
    try:
        pdf_file = genai.upload_file(path=file_path)
        
        # Wait for file to be processed
        while pdf_file.state.name == "PROCESSING":
            print("Waiting for file to be processed...")
            time.sleep(2)
            pdf_file = genai.get_file(pdf_file.name)
            
    except Exception as e:
        print(f"Failed to upload file to Gemini: {e}")
        return None
        
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
    
    print("Generating content from PDF using Gemini...")
    
    # Implement Exponential Backoff for 429 errors
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content([pdf_file, prompt])
            content_text = response.text
            
            # Simple cleanup if the response is wrapped in markdown json block
            if "```json" in content_text:
                content_text = content_text.split("```json")[1].split("```")[0]
            elif "```" in content_text:
                content_text = content_text.split("```")[1].split("```")[0]
                
            extracted_data = json.loads(content_text.strip())
            return extracted_data
            
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                print(f"Rate limit hit (429). Attempt {attempt + 1}/{max_retries}. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                print(f"Error generating content: {e}")
                break
                
    return None
