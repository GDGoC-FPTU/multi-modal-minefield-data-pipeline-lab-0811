"""HTML Processing Module: Extract product catalog data from HTML tables.

Parses HTML documents containing structured product tables with:
- Product IDs and names
- Categories and pricing
- Stock levels and customer ratings

Author: ETL/ELT Builder (Role 2)
"""

from bs4 import BeautifulSoup
import logging
import os

logger = logging.getLogger(__name__)

# ==========================================
# ROLE 2: ETL/ELT BUILDER
# ==========================================
# Task: Extract product data from the HTML table, ignoring boilerplate.

def parse_html_catalog(file_path):
    """Parse product catalog from HTML table.
    
    Expects HTML structure with table id='main-catalog' containing:
    Columns: product_id, name, category, price, stock, [rating]
    
    Args:
        file_path (str): Path to HTML file
        
    Returns:
        list: List of UnifiedDocument-compatible dicts for each product.
              Returns empty list if file missing, table not found, or parsing fails.
              
    Raises:
        Exception: Caught and logged; returns empty list instead of crashing
    """
    # Validate file
    if not os.path.exists(file_path):
        logger.error(f"HTML file not found: {file_path}")
        return []
    
    if not file_path.lower().endswith(('.html', '.htm')):
        logger.warning(f"File {file_path} is not HTML. Attempting to parse anyway.")
    
    # Parse HTML with error handling
    logger.info(f"Reading HTML file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
    except Exception as e:
        logger.error(f"Failed to parse HTML: {e}")
        return []
    
    # 1. Find the table with id 'main-catalog'
    table = soup.find('table', id='main-catalog')
    if not table:
        logger.warning("No table with id='main-catalog' found in HTML")
        # Try to find any table as fallback
        table = soup.find('table')
        if not table:
            logger.error("No tables found in HTML at all")
            return []
        logger.info("Using first available table as fallback")
    
    # Validate table structure
    tbody = table.find('tbody')
    if not tbody:
        logger.warning("Table has no <tbody> tag, searching for <tr> directly")
        rows = table.find_all('tr')
    else:
        rows = tbody.find_all('tr')
    
    if not rows:
        logger.warning("No rows found in HTML table")
        return []
    
    # 2. Extract rows with validation
    unified_docs = []
    parse_errors = 0
    logger.info(f"Found {len(rows)} rows in table")
    
    for row_idx, row in enumerate(rows):
        cols = row.find_all('td')
        if len(cols) < 5:
            logger.debug(f"Row {row_idx} has only {len(cols)} columns (need >= 5), skipping")
            continue
        
        try:
            sp_id = cols[0].text.strip()
            name = cols[1].text.strip()
            category = cols[2].text.strip()
            price_raw = cols[3].text.strip()
            stock = cols[4].text.strip()
            rating = cols[5].text.strip() if len(cols) > 5 else "N/A"
            
            # Validate required fields
            if not sp_id or not name:
                logger.warning(f"Row {row_idx} missing product ID or name, skipping")
                continue
            
            # Clean price (similar logic to CSV but simpler for HTML content)
            price_clean = price_raw.replace(",", "").replace(" VND", "").strip()
            if price_clean in ["N/A", "Liên hệ", "-", ""]:
                price_numeric = 0.0
            else:
                try:
                    price_numeric = float(price_clean)
                except ValueError:
                    logger.debug(f"Could not parse price '{price_raw}' in row {row_idx}")
                    price_numeric = 0.0
            
            # Validate stock value
            try:
                stock_int = int(stock) if stock.isdigit() else 0
            except (ValueError, AttributeError):
                stock_int = 0
                
            doc = {
                "document_id": f"html-{sp_id}",
                "content": f"Product: {name}. Category: {category}. Price: {price_numeric} VND. Stock: {stock_int}. Rating: {rating}",
                "source_type": "HTML",
                "author": "VinShop Catalog",
                "timestamp": None,
                "source_metadata": {
                    "price_raw": price_raw,
                    "price_numeric": float(price_numeric),
                    "stock": stock_int,
                    "rating": rating,
                    "is_table_data": True
                }
            }
            unified_docs.append(doc)
        except Exception as e:
            logger.error(f"Error parsing HTML row {row_idx}: {e}")
            parse_errors += 1
            continue
    
    logger.info(f"Extracted {len(unified_docs)} products from HTML ({parse_errors} parsing errors)")
    return unified_docs

