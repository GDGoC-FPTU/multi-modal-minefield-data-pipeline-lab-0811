"""Orchestrator Module: Main pipeline coordination and execution.

Coordinates the entire multi-modal data ingestion pipeline:
- Manages file paths and input/output handling
- Calls all processing modules (PDF, CSV, HTML, Transcript, Code)
- Applies quality gates to all documents
- Aggregates results and measures SLA performance
- Saves final knowledge base to JSON

Author: DevOps & Integration Specialist (Role 4)
"""

import json
import time
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    """Execute the complete data pipeline.
    
    Pipeline stages:
    1. Initialize: Log config, validate paths
    2. Process: Run all 5 data source processors
    3. Validate: Apply quality gates
    4. Aggregate: Combine valid documents
    5. Persist: Save to JSON output
    6. Report: Log metrics and performance
    """
    start_time = time.time()
    final_kb = []
    
    logger.info("=" * 60)
    logger.info("STARTING DATA PIPELINE ORCHESTRATION")
    logger.info("=" * 60)
    logger.info(f"Raw data directory: {RAW_DATA_DIR}")
    
    # --- FILE PATH SETUP (Handled for students) ---
    pdf_path = os.path.join(RAW_DATA_DIR, "lecture_notes.pdf")
    trans_path = os.path.join(RAW_DATA_DIR, "demo_transcript.txt")
    html_path = os.path.join(RAW_DATA_DIR, "product_catalog.html")
    csv_path = os.path.join(RAW_DATA_DIR, "sales_records.csv")
    code_path = os.path.join(RAW_DATA_DIR, "legacy_pipeline.py")
    
    output_path = os.path.join(os.path.dirname(SCRIPT_DIR), "processed_knowledge_base.json")
    
    # Validate input files exist
    input_files = {
        "PDF": pdf_path,
        "Transcript": trans_path,
        "HTML": html_path,
        "CSV": csv_path,
        "Code": code_path
    }
    
    logger.info("Validating input files:")
    for file_type, file_path in input_files.items():
        exists = "✓" if os.path.exists(file_path) else "✗"
        logger.info(f"  {exists} {file_type}: {file_path}")
    
    logger.info("-" * 60)

    # TODO: Call each processing function (extract_pdf_data, clean_transcript, etc.)
    # Call processors, run quality gates, and collect validated docs
    def _validate_and_append(candidate, source_name="Unknown"):
        """Validate and append document to knowledge base.
        
        Args:
            candidate: Raw document dict from processor
            source_name: Human-readable source name for logging
            
        Returns:
            bool: True if document was added, False if rejected
        """
        if not candidate or not isinstance(candidate, dict):
            logger.warning(f"[{source_name}] Invalid candidate: None or not dict")
            return False
        
        doc_id = candidate.get('document_id', '<unknown>')
        
        # Apply quality gate
        if not run_quality_gate(candidate):
            logger.warning(f"[{source_name}] {doc_id}: REJECTED by quality gate")
            return False
        
        # Validate against schema
        try:
            doc = UnifiedDocument(**candidate)
            # Use mode='json' to ensure datetime objects are serialized to strings
            final_kb.append(doc.model_dump(mode='json'))
            logger.info(f"[{source_name}] ✓ {doc.document_id} ({doc.source_type}) - ACCEPTED")
            return True
        except Exception as e:
            logger.error(f"[{source_name}] {doc_id}: Schema validation failed - {e}")
            return False

    # Processing statistics
    processor_stats = {
        "pdf": {"attempted": 0, "success": 0},
        "transcript": {"attempted": 0, "success": 0},
        "html": {"attempted": 0, "success": 0},
        "csv": {"attempted": 0, "success": 0},
        "code": {"attempted": 0, "success": 0}
    }

    # Process PDF
    try:
        logger.info("PROCESSING: PDF Document")
        processor_stats["pdf"]["attempted"] = 1
        pdf_doc = extract_pdf_data(pdf_path)
        if _validate_and_append(pdf_doc, "PDF"):
            processor_stats["pdf"]["success"] = 1
    except Exception as e:
        logger.error(f"CRITICAL: Error processing PDF: {e}")

    # Process Transcript
    try:
        logger.info("PROCESSING: Transcript")
        processor_stats["transcript"]["attempted"] = 1
        trans_doc = clean_transcript(trans_path)
        if _validate_and_append(trans_doc, "Transcript"):
            processor_stats["transcript"]["success"] = 1
    except Exception as e:
        logger.error(f"CRITICAL: Error processing Transcript: {e}")

    # Process HTML catalog (may return list)
    try:
        logger.info("PROCESSING: HTML Catalog")
        processor_stats["html"]["attempted"] = 1
        html_docs = parse_html_catalog(html_path)
        if isinstance(html_docs, dict):
            html_docs = [html_docs]
        success_count = 0
        for d in (html_docs or []):
            if _validate_and_append(d, "HTML"):
                success_count += 1
        processor_stats["html"]["success"] = success_count
        logger.info(f"HTML: Processed {len(html_docs or [])} products, {success_count} passed QA")
    except Exception as e:
        logger.error(f"CRITICAL: Error processing HTML catalog: {e}")

    # Process CSV sales (may return list)
    try:
        logger.info("PROCESSING: CSV Sales Records")
        processor_stats["csv"]["attempted"] = 1
        csv_docs = process_sales_csv(csv_path)
        if isinstance(csv_docs, dict):
            csv_docs = [csv_docs]
        success_count = 0
        for d in (csv_docs or []):
            if _validate_and_append(d, "CSV"):
                success_count += 1
        processor_stats["csv"]["success"] = success_count
        logger.info(f"CSV: Processed {len(csv_docs or [])} records, {success_count} passed QA")
    except Exception as e:
        logger.error(f"CRITICAL: Error processing CSV: {e}")

    # Process legacy code
    try:
        logger.info("PROCESSING: Legacy Code")
        processor_stats["code"]["attempted"] = 1
        code_doc = extract_logic_from_code(code_path)
        if _validate_and_append(code_doc, "Code"):
            processor_stats["code"]["success"] = 1
    except Exception as e:
        logger.error(f"CRITICAL: Error processing legacy code: {e}")

    # Save final_kb to disk
    logger.info("-" * 60)
    logger.info("AGGREGATION & PERSISTENCE")
    logger.info("-" * 60)
    
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_kb, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✓ Knowledge base saved: {output_path}")
        logger.info(f"  Total documents: {len(final_kb)}")
        logger.info(f"  File size: {os.path.getsize(output_path) / 1024:.1f} KB")
    except Exception as e:
        logger.error(f"CRITICAL: Failed to write output file {output_path}: {e}")
        return

    # Final reporting
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    logger.info("-" * 60)
    logger.info("PIPELINE SUMMARY & METRICS")
    logger.info("-" * 60)
    
    total_attempted = sum(s["attempted"] for s in processor_stats.values())
    total_success = sum(s["success"] for s in processor_stats.values())
    
    logger.info("Processor Status:")
    for processor, stats in processor_stats.items():
        status = "✓" if stats["success"] > 0 else "✗"
        logger.info(f"  {status} {processor.upper():12s} - Attempted: {stats['attempted']}, Processed: {stats['success']}")
    
    logger.info("")
    logger.info(f"Processing Time: {elapsed_time:.2f} seconds")
    logger.info(f"Total Documents: {len(final_kb)}")
    logger.info(f"Documents per second: {len(final_kb) / max(elapsed_time, 0.01):.1f}")
    logger.info("")
    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETED SUCCESSFULLY")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
