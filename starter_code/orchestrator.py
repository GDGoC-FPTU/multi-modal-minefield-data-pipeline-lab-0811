import json
import time
import os

# Robust path handling
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "raw_data")


# Import role-specific modules
from schema import UnifiedDocument
from process_pdf import extract_pdf_data
from process_transcript import clean_transcript
from process_html import parse_html_catalog
from process_csv import process_sales_csv
from process_legacy_code import extract_logic_from_code
from quality_check import run_quality_gate

# ==========================================
# ROLE 4: DEVOPS & INTEGRATION SPECIALIST
# ==========================================
# Task: Orchestrate the ingestion pipeline and handle errors/SLA.

def main():
    start_time = time.time()
    final_kb = []
    
    # --- FILE PATH SETUP (Handled for students) ---
    pdf_path = os.path.join(RAW_DATA_DIR, "lecture_notes.pdf")
    trans_path = os.path.join(RAW_DATA_DIR, "demo_transcript.txt")
    html_path = os.path.join(RAW_DATA_DIR, "product_catalog.html")
    csv_path = os.path.join(RAW_DATA_DIR, "sales_records.csv")
    code_path = os.path.join(RAW_DATA_DIR, "legacy_pipeline.py")
    
    output_path = os.path.join(os.path.dirname(SCRIPT_DIR), "processed_knowledge_base.json")
    # ----------------------------------------------

    # TODO: Call each processing function (extract_pdf_data, clean_transcript, etc.)
    # Call processors, run quality gates, and collect validated docs
    def _validate_and_append(candidate):
        if not candidate or not isinstance(candidate, dict):
            return False
        if not run_quality_gate(candidate):
            print(f"Rejected by quality gate: {candidate.get('document_id', '<unknown>')}")
            return False
        try:
            doc = UnifiedDocument(**candidate)
            final_kb.append(doc.dict())
            print(f"Added: {doc.document_id} ({doc.source_type})")
            return True
        except Exception as e:
            print(f"Validation failed for {candidate.get('document_id', '<unknown>')}: {e}")
            return False

    # Process PDF
    try:
        pdf_doc = extract_pdf_data(pdf_path)
        _validate_and_append(pdf_doc)
    except Exception as e:
        print(f"Error processing PDF: {e}")

    # Process Transcript
    try:
        trans_doc = clean_transcript(trans_path)
        _validate_and_append(trans_doc)
    except Exception as e:
        print(f"Error processing Transcript: {e}")

    # Process HTML catalog (may return list)
    try:
        html_docs = parse_html_catalog(html_path)
        if isinstance(html_docs, dict):
            html_docs = [html_docs]
        for d in (html_docs or []):
            _validate_and_append(d)
    except Exception as e:
        print(f"Error processing HTML catalog: {e}")

    # Process CSV sales (may return list)
    try:
        csv_docs = process_sales_csv(csv_path)
        if isinstance(csv_docs, dict):
            csv_docs = [csv_docs]
        for d in (csv_docs or []):
            _validate_and_append(d)
    except Exception as e:
        print(f"Error processing CSV: {e}")

    # Process legacy code
    try:
        code_doc = extract_logic_from_code(code_path)
        _validate_and_append(code_doc)
    except Exception as e:
        print(f"Error processing legacy code: {e}")

    # Save final_kb to disk
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_kb, f, ensure_ascii=False, indent=2)
        print(f"Pipeline finished! Saved {len(final_kb)} records to {output_path}")
    except Exception as e:
        print(f"Failed to write output file {output_path}: {e}")

    end_time = time.time()
    print(f"Pipeline finished in {end_time - start_time:.2f} seconds.")
    print(f"Total valid documents stored: {len(final_kb)}")


if __name__ == "__main__":
    main()
