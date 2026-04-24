from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

# ==========================================
# ROLE 1: LEAD DATA ARCHITECT
# ==========================================
# Your task is to define the Unified Schema for all sources.
# This is v1. Note: A breaking change is coming at 11:00 AM!

class UnifiedDocument(BaseModel):
    document_id: str = Field(..., description="Unique ID for the document (e.g., pdf-001, csv-102)")
    content: str = Field(..., description="The main extracted text or content")
    source_type: str = Field(..., description="Type of the source, e.g., 'PDF', 'Video', 'HTML', 'CSV', 'Code'")
    author: Optional[str] = Field(default="Unknown", description="Author or speaker of the document")
    timestamp: Optional[datetime] = Field(default=None, description="Time of extraction or the document's original time")

    # Using a flexible dict for source-specific metadata (e.g., 'detected_price_vnd' for video, 'tables' for HTML)
    source_metadata: Dict[str, Any] = Field(default_factory=dict, description="Source-specific metadata")

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
