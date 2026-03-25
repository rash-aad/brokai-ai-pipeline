from ddgs import DDGS
import requests
from bs4 import BeautifulSoup
import time
import re


def search_company_web(company_name, location, max_results=3):
    """Searches DuckDuckGo for the company and returns top URLs and snippets."""
    query = f"{company_name} {location} official website OR overview"
    print(f"🔍 Searching web for: {query}")
    
    results = []
    try:
        # Using the new ddgs syntax
        search_results = DDGS().text(query, max_results=max_results)
        
        # Check if we got results back
        if search_results:
            for res in search_results:
                results.append({
                    "title": res.get("title", ""),
                    "url": res.get("href", ""),
                    "snippet": res.get("body", "")
                })
        return results
    except Exception as e:
        print(f"⚠️ Search error for {company_name}: {e}")
        return []

def scrape_website_text(url, max_chars=3000):
    """Fetches a URL and extracts visible text to feed to the LLM."""
    try:
        # Use a generic User-Agent so websites don't block our free scraper
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for script in soup(["script", "style"]):
                script.extract()
                
            text = soup.get_text(separator=' ', strip=True)
            return text[:max_chars]
        else:
            return f"Failed to access URL. Status code: {response.status_code}"
    except Exception as e:
        return f"Scraping failed: {e}"
    
def search_contact_info(company_name, location, max_results=6):
    """Searches specifically for contact pages and directory listings."""
    
    # CLEAN QUERY: No 'OR' operators. Just the company, location, and the data we want.
    query = f"{company_name} {location} contact number email"
    
    print(f"🔍 Searching web for contact info: {query}")
    
    results = []
    try:
        from ddgs import DDGS
        # We grab 6 results so our Agent 02 sorter has plenty of links to evaluate
        search_results = DDGS().text(query, max_results=max_results)
        if search_results:
            for res in search_results:
                results.append({
                    "title": res.get("title", ""),
                    "url": res.get("href", ""),
                    "snippet": res.get("body", "")
                })
        return results
    except Exception as e:
        print(f"⚠️ Contact search error: {e}")
        return []

def scrape_website_text(url, max_chars=3000):
    """Fetches a URL, extracts visible text, hidden emails, and regex-hunts for phones."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            raw_html = response.text
            
            # --- THE "INSPECT ELEMENT" HACK ---
            # Before we clean the HTML, scan the raw code for Indian mobile numbers (10 digits starting with 6-9)
            hidden_phones = set(re.findall(r'\b[6-9]\d{9}\b', raw_html))
            
            soup = BeautifulSoup(raw_html, 'html.parser')
            
            for script in soup(["script", "style"]):
                script.extract()
                
            text = soup.get_text(separator=' ', strip=True)
            
            # Extract mailto links
            emails_found = []
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if href.startswith('mailto:'):
                    clean_email = href.replace('mailto:', '').split('?')[0]
                    if clean_email not in emails_found:
                        emails_found.append(clean_email)
            
            # Append our sneaky discoveries to the bottom of the text for the LLM to read
            extracted_secrets = ""
            if emails_found:
                extracted_secrets += "\n\n=== HIDDEN EMAILS FOUND ===\n" + ", ".join(emails_found)
            if hidden_phones:
                extracted_secrets += "\n\n=== HIDDEN PHONES FOUND IN SOURCE CODE ===\n" + ", ".join(hidden_phones)
                
            final_text = text[:max_chars] + extracted_secrets
            return final_text
        else:
            return f"Failed to access URL. Status code: {response.status_code}"
    except Exception as e:
        return f"Scraping failed: {e}"