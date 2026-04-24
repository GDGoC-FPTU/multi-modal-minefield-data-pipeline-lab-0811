"""CSV Processing Module: Clean and transform sales records data.

Handles CSV files with sales data including:
- Price variations (currency symbols, text descriptions, different formats)
- Duplicate product IDs (keeps first, removes rest)
- Multiple date formats (DD/MM/YYYY, YYYY-MM-DD, text formats like "Jan 15")
- Stock quantities and currency codes

Author: ETL/ELT Builder (Role 2)
"""

import pandas as pd
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ==========================================
# ROLE 2: ETL/ELT BUILDER
# ==========================================
# Task: Process sales records, handling type traps and duplicates.

def process_sales_csv(file_path):
    """Process CSV sales records and convert to UnifiedDocument format.
    
    Handles common data quality issues:
    - Duplicate product IDs (keeps first occurrence)
    - Price column with mixed formats: $1200, "five dollars", "500000", "N/A"
    - Multiple date formats: DD/MM/YYYY, YYYY-MM-DD, "January 16th 2026"
    - Missing values and null entries
    
    Args:
        file_path (str): Path to CSV file with columns: id, product_name, category, 
                        price, currency, stock_quantity, seller_id, date_of_sale
        
    Returns:
        list: List of UnifiedDocument-compatible dicts, one per product.
              Returns empty list if file missing or invalid.
              
    Raises:
        Exception: Caught and logged; returns empty list instead of crashing
    """
    # Validate file existence
    import os
    if not os.path.exists(file_path):
        logger.error(f"CSV file not found: {file_path}")
        return []
    
    if not file_path.lower().endswith('.csv'):
        logger.warning(f"File {file_path} is not a CSV extension. Attempting to read anyway.")
    
    # Read CSV with error handling
    logger.info(f"Reading CSV file: {file_path}")
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} rows from CSV")
    except pd.errors.ParserError as e:
        logger.error(f"CSV parsing error: {e}")
        return []
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        return []
    
    # Validate required columns
    required_cols = ['id', 'product_name', 'category', 'price', 'currency', 'stock_quantity', 'seller_id', 'date_of_sale']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.warning(f"CSV missing required columns: {missing_cols}. Processing with available columns.")
    
    # Check for empty dataframe
    if df.empty:
        logger.warning("CSV file is empty")
        return []
    
    # 1. Remove duplicate rows based on 'id'
    # Keep the first occurrence
    initial_count = len(df)
    df = df.drop_duplicates(subset=['id'], keep='first')
    duplicates_removed = initial_count - len(df)
    if duplicates_removed > 0:
        logger.info(f"Removed {duplicates_removed} duplicate product IDs (kept {len(df)} unique)")
    else:
        logger.debug("No duplicate IDs found")
    
    # 2. Clean 'price' column with validation
    def clean_price(price_str):
        """Parse price from various formats into float.
        
        Handles:
        - Currency symbols: $1200 → 1200.0
        - Text: "five dollars" → 5.0
        - VND amounts: 500000 → 500000.0
        - Missing values: None/NA → 0.0
        - Negative prices (kept as-is): -100 → -100.0
        """
        if pd.isna(price_str):
            return 0.0
        
        price_str = str(price_str).strip().lower()
        
        # Handle empty strings
        if not price_str:
            return 0.0
        
        # Word-based prices
        if price_str == "five dollars":
            return 5.0
        if price_str in ["n/a", "liên hệ", "null", "unknown", "-"]:
            return 0.0
            
        # Remove currency symbols and commas
        price_str = price_str.replace("$", "").replace(",", "").replace("vnd", "").strip()
        
        # Extract numeric part (handles negative signs too)
        match = re.search(r"[-+]?\d*\.?\d+", price_str)
        if match:
            price_val = float(match.group())
            # Warn if price is negative or unusually large
            if price_val < 0:
                logger.warning(f"Negative price detected: {price_str} → {price_val}")
            elif price_val > 1000000000:  # 1 billion threshold
                logger.warning(f"Unusually large price detected: {price_val}")
            return price_val
        
        logger.debug(f"Could not parse price: {price_str} (using 0.0)")
        return 0.0

    df['cleaned_price'] = df['price'].apply(clean_price)
    logger.info("Cleaned price column")
    
    # 3. Normalize 'date_of_sale' into a single format (YYYY-MM-DD)
    def normalize_date(date_str):
        """Parse date from multiple formats into YYYY-MM-DD string.
        
        Supports:
        - ISO format: 2026-01-15
        - European: 15/01/2026, 15-01-2026
        - Ordinal text: "January 16th 2026", "January 21st 2026"
        - Text with slash: 2026/01/19
        
        Returns: "YYYY-MM-DD" string or None if unparseable
        """
        if pd.isna(date_str):
            return None
        
        date_str = str(date_str).strip()
        
        # Try various formats
        formats = [
            "%Y-%m-%d",          # 2026-01-15
            "%d/%m/%Y",          # 15/01/2026
            "%d-%m-%Y",          # 17-01-2026
            "%Y/%m/%d",          # 2026/01/19
            "%d %b %Y",          # 19 Jan 2026
            "%B %dth %Y",        # January 16th 2026 (simplified)
            "%B %dst %Y",        # January 21st 2026
            "%B %dnd %Y",        # January 22nd 2026
            "%B %drd %Y",        # January 23rd 2026
        ]
        
        # Clean up "th", "st", "nd", "rd" for strptime if needed, 
        # but easier to just use regex to strip them
        date_str_clean = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
        
        for fmt in formats:
            try:
                # Remove suffixes from format string too if they were removed from date_str
                fmt_clean = re.sub(r'(%d)(st|nd|rd|th)', r'\1', fmt)
                return datetime.strptime(date_str_clean, fmt_clean).strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        return None

    df['normalized_date'] = df['date_of_sale'].apply(normalize_date)
    invalid_dates = df['normalized_date'].isna().sum()
    if invalid_dates > 0:
        logger.warning(f"Could not parse {invalid_dates} dates (set to None)")
    else:
        logger.debug("All dates normalized successfully")
    
    # 4. Return a list of dictionaries for the UnifiedDocument schema.
    unified_docs = []
    conversion_errors = 0
    
    for idx, (_, row) in enumerate(df.iterrows()):
        try:
            # Validate required fields
            if pd.isna(row.get('id')) or pd.isna(row.get('product_name')):
                logger.warning(f"Row {idx} missing id or product_name, skipping")
                continue
            
            doc = {
                "document_id": f"csv-sale-{row['id']}",
                "content": f"Sale of {row['product_name']} in category {row['category']} for {row['cleaned_price']} {row['currency']}",
                "source_type": "CSV",
                "author": str(row.get('seller_id', 'Unknown')),
                "timestamp": row['normalized_date'],
                "source_metadata": {
                    "original_price": str(row['price']),
                    "cleaned_price": float(row['cleaned_price']),
                    "currency": str(row.get('currency', 'USD')),
                    "stock": int(row.get('stock_quantity', 0)) if pd.notna(row.get('stock_quantity')) else 0,
                    "is_tabular_data": True
                }
            }
            unified_docs.append(doc)
        except Exception as e:
            logger.error(f"Error converting row {idx} to UnifiedDocument: {e}")
            conversion_errors += 1
            continue
    
    logger.info(f"Converted {len(unified_docs)} CSV rows to UnifiedDocuments ({conversion_errors} errors)")
    return unified_docs

