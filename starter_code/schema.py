"""Schema Module: Unified Document Structure for Multi-Modal Data Pipeline.

Defines the core data model (UnifiedDocument) that all input sources must conform to.
This schema is designed to be flexible enough to handle diverse data types (PDF, CSV, HTML,
video transcripts, and legacy code) while maintaining consistency across the pipeline.

VERSION: v1 (Breaking change v2 expected at 11:00 AM)
Author: Lead Data Architect (Role 1)
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# ==========================================
# ROLE 1: LEAD DATA ARCHITECT
# ==========================================
# Your task is to define the Unified Schema for all sources.
# This is v1. Note: A breaking change is coming at 11:00 AM!

class UnifiedDocument(BaseModel):
    """Unified document structure for all data sources in the knowledge base pipeline.
    
    This schema accommodates diverse data types:
    - PDFs: lecture notes with tables
    - CSVs: sales records with pricing
    - HTML: product catalogs  
    - Video transcripts: with timestamps and price mentions
    - Legacy code: with business logic and docstrings
    
    Fields:
        document_id: Unique identifier using source-prefix format (e.g., 'pdf-001', 'csv-102', 'html-p123')
        content: Main text/summary extracted from source. Minimum 20 chars for quality gate.
        source_type: Classification of data source ('PDF', 'CSV', 'HTML', 'Video', 'Code')
        author: Person/entity responsible (e.g., speaker, seller ID, system)
        timestamp: Document creation/processing time. ISO 8601 format preferred.
        source_metadata: Flexible dict for type-specific info (prices, tables, rules, etc.)
    """
    document_id: str = Field(..., description="Unique ID for the document (e.g., pdf-001, csv-102)")
    content: str = Field(..., description="The main extracted text or content (minimum 20 chars)")
    source_type: str = Field(..., description="Type of the source, e.g., 'PDF', 'Video', 'HTML', 'CSV', 'Code'")
    author: Optional[str] = Field(default="Unknown", description="Author or speaker of the document")
    timestamp: Optional[datetime] = Field(default=None, description="Time of extraction or the document's original time")

    # Using a flexible dict for source-specific metadata (e.g., 'detected_price_vnd' for video, 'tables' for HTML)
    # This allows extensibility without schema changes for each new field
    source_metadata: Dict[str, Any] = Field(default_factory=dict, description="Source-specific metadata (flexible structure)")

    # Pydantic configuration to anticipate v2 schema migration (e.g., field renaming)
    # allowing us to use Field(alias='old_name') later without breaking existing pipelines.
    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "document_id": "csv-001",
                "content": "Sales data for Q1",
                "source_type": "CSV",
                "author": "System",
                "source_metadata": {"rows_processed": 100}
            }
        }
    }

    # For Pydantic v1 compatibility if using an older version:
    # class Config:
    #     allow_population_by_field_name = True
