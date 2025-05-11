data_percentage_add = 10
import re
def extractDataSize(arr):
        # print(arr)
    match = re.search(r'(\d+(\.\d+)?)(\s?)(TB|GB|MB)', arr.upper())
    if match:
        return match.group(0).strip()
    return None
    
    
def add_commision(price):
    price=float(price)
    return price+price*(data_percentage_add/100)

def extract_size_name(item):
    text = str(item).lower()
    qty = extractDataSize(text)

    # Extract duration
    duration = 'daily'  # default fallback

    if re.search(r'\b\d+\s*(day|days)\b', text) or 'hrs' in text:
        duration = 'daily'
    
    elif re.search(r'\b\d+\s*(2day|2-days|2Day|2Days)\b', text) or '2 days' in text or '2days' in text:
        duration = '2 days'
    elif re.search(r'\b\d+\s*(week|weeks|weekly|Weekly)\b', text) or '7days' in text or '7 days' in text:
        duration = 'weekly'
    elif re.search(r'\b\d+\s*(month|months)\b',text) or '30days' in text or '30 days' or "Monthly" or "monthly" in text:
        duration = 'monthly'
    elif re.search(r'\b\d+\s*(month|months)\b',text) or '2-Months' in text or "2-Month" in text or '2 Months' in text or "2 months" in text:
        duration = '2 Months'
    elif re.search(r'\b\d+\s*(year|years)\b', text):
        duration = '1 year'

    return duration, qty