import os
from google import genai
from google.genai import types
from pydantic import BaseModel
from utils.search_tools import search_contact_info, scrape_website_text
from dotenv import load_dotenv

load_dotenv()

# The strict output structure required by the assessment
class ContactCard(BaseModel):
    contact_found: bool  # This is our graceful failure trigger!
    email: str
    phone: str
    whatsapp: str
    source_url: str

def run_contact_finder_agent(company_name, location):
    """Agent 02: Scours directories and websites for contact information."""
    print(f"\n📞 [Agent 02] Hunting for contact info: {company_name}...")
    
    # 1. Gather raw contact data from the web
    search_results = search_contact_info(company_name, location)
    
    # --- THE PRIORITY SORTING HACK ---
    # We force the highest quality registry sites to the top of the list so they never get skipped.
    priority_domains = ['companydetails.in', 'falconebiz.com', 'tofler.in', 'justdial.com']
    search_results = sorted(
        search_results, 
        key=lambda x: any(domain in x['url'].lower() for domain in priority_domains), 
        reverse=True
    )
    
    scraped_context = "=== SEARCH ENGINE SNIPPETS ===\n"
    for res in search_results:
        scraped_context += f"Source URL: {res['url']}\nSnippet: {res['snippet']}\n\n"

    scraped_context += "=== SCRAPED WEBSITE TEXT ===\n"
    
    # INCREASED LIMIT: We now scrape the top 3 links to cast a wider net
    for i, result in enumerate(search_results[:3]):
        url = result['url']
        print(f"   📄 Checking for numbers/emails at: {url}")
        page_text = scrape_website_text(url)
        
        if len(page_text) < 200 or "Access Denied" in page_text or "Security" in page_text:
             print("   ⚠️ Directory blocked the scraper. Relying entirely on DDG snippets.")
        else:
             print("   ✅ Scrape successful.")
             scraped_context += f"\n--- Text from {url} ---\n{page_text}\n"

    # --- THE DEBUG LOGGER ---
    with open("debug_scraped_context.txt", "w", encoding="utf-8") as f:
        f.write(scraped_context)
    print("   💾 [Debug] Saved raw scraped text to 'debug_scraped_context.txt' for inspection.")

    # 2. Prepare the prompt
    prompt = f"""
    You are an expert lead researcher. Find the contact information for '{company_name}' located in '{location}'.
    
    Review the following search snippets and website text to extract:
    1. Email address
    2. Phone number
    3. WhatsApp number (if explicitly mentioned)
    4. The exact Source URL where you found the most useful contact data.
    
    CRITICAL ANTI-HALLUCINATION RULES:
    - NEVER guess or invent an email address based on a person's name or domain.
    - If an email address is listed as "[email protected]", it means it is hidden by security. You MUST output "Not publicly available" for the email.
    - MULTIPLE NUMBERS: If you find multiple potential phone numbers in the text or source code, list ALL of them separated by commas. Do not just pick one.
    - If you are not 100% certain the contact info is explicitly written in the data, output "Not publicly available".
    - If you cannot find ANY valid contact info, set 'contact_found' to false.
    
    Raw Data:
    {scraped_context}
    """

    # 3. Call the Gemini API
    try:
        client = genai.Client()
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ContactCard,
                temperature=0.1 
            ),
        )
        
        print("✅ [Agent 02] Contact search complete.")
        import json
        return json.loads(response.text)
        
    except Exception as e:
        print(f"❌ [Agent 02] LLM Error: {e}")
        return {
            "contact_found": False,
            "email": "Error",
            "phone": "Error",
            "whatsapp": "Error",
            "source_url": "Error"
        }

# --- Quick Test Block ---
if __name__ == "__main__":
    # Let's test it on the same company!
    test_contact = run_contact_finder_agent("URJASVINI SOLUTION OPC PRIVATE LIMITED", "RAJASTHAN")
    if test_contact:
        print("\n--- Final Contact Card ---")
        for key, value in test_contact.items():
            print(f"**{key}**: {value}")