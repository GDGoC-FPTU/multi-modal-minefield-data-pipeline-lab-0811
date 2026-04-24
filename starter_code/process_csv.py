import pandas as pd
import re
from datetime import datetime

# ==========================================
# ROLE 2: ETL/ELT BUILDER
# ==========================================
# Task: Process sales records, handling type traps and duplicates.

def process_sales_csv(file_path):
    # --- FILE READING (Handled for students) ---
    df = pd.read_csv(file_path)
    # ------------------------------------------
    
    # 1. Remove duplicate rows based on 'id'
    # Keep the first occurrence
    df = df.drop_duplicates(subset=['id'], keep='first')
    
    # 2. Clean 'price' column
    def clean_price(price_str):
        if pd.isna(price_str):
            return 0.0
        
        price_str = str(price_str).strip().lower()
        
        # Word-based prices
        if price_str == "five dollars":
            return 5.0
        if price_str in ["n/a", "liên hệ", "null"]:
            return 0.0
            
        # Remove currency symbols and commas
        price_str = price_str.replace("$", "").replace(",", "")
        
        # Extract numeric part (handles negative signs too)
        match = re.search(r"[-+]?\d*\.?\d+", price_str)
        if match:
            return float(match.group())
        return 0.0

    df['cleaned_price'] = df['price'].apply(clean_price)
    
    # 3. Normalize 'date_of_sale' into a single format (YYYY-MM-DD)
    def normalize_date(date_str):
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
    
    # 4. Return a list of dictionaries for the UnifiedDocument schema.
    unified_docs = []
    for _, row in df.iterrows():
        doc = {
            "document_id": f"csv-sale-{row['id']}",
            "content": f"Sale of {row['product_name']} in category {row['category']}",
            "source_type": "CSV",
            "author": str(row['seller_id']),
            "timestamp": row['normalized_date'],
            "source_metadata": {
                "original_price": row['price'],
                "cleaned_price": row['cleaned_price'],
                "currency": row['currency'],
                "stock": row['stock_quantity'],
                "is_tabular_data": True
            }
        }
        unified_docs.append(doc)
    
    return unified_docs

