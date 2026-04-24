from bs4 import BeautifulSoup

# ==========================================
# ROLE 2: ETL/ELT BUILDER
# ==========================================
# Task: Extract product data from the HTML table, ignoring boilerplate.

def parse_html_catalog(file_path):
    # --- FILE READING (Handled for students) ---
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    # ------------------------------------------
    
    # 1. Find the table with id 'main-catalog'
    table = soup.find('table', id='main-catalog')
    if not table:
        return []
    
    # 2. Extract rows
    unified_docs = []
    rows = table.find('tbody').find_all('tr')
    
    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 5:
            continue
            
        sp_id = cols[0].text.strip()
        name = cols[1].text.strip()
        category = cols[2].text.strip()
        price_raw = cols[3].text.strip()
        stock = cols[4].text.strip()
        rating = cols[5].text.strip() if len(cols) > 5 else "N/A"
        
        # Clean price (similar logic to CSV but simpler for HTML content)
        price_clean = price_raw.replace(",", "").replace(" VND", "")
        if price_clean in ["N/A", "Liên hệ"]:
            price_numeric = 0.0
        else:
            try:
                price_numeric = float(price_clean)
            except ValueError:
                price_numeric = 0.0
                
        doc = {
            "document_id": f"html-{sp_id}",
            "content": f"Product: {name}. Category: {category}. Rating: {rating}",
            "source_type": "HTML",
            "author": "VinShop Catalog",
            "timestamp": None,
            "source_metadata": {
                "price_raw": price_raw,
                "price_numeric": price_numeric,
                "stock": stock,
                "rating": rating,
                "is_table_data": True
            }
        }
        unified_docs.append(doc)
    
    return unified_docs

