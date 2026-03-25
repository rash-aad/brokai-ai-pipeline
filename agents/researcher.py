import os
from google import genai
from google.genai import types
from pydantic import BaseModel
from utils.search_tools import search_company_web, scrape_website_text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the strict output structure
class BusinessProfile(BaseModel):
    summary: str
    size_signals: str
    digital_presence: str
    tools_used: str

def run_researcher_agent(company_name, location):
    """Agent 01: Researches a company and returns a structured business profile."""
    print(f"\n🤖 [Agent 01] Researching: {company_name}...")
    
    # 1. Gather raw data from the web
    search_results = search_company_web(company_name, location)
    
    scraped_context = "=== SEARCH ENGINE SNIPPETS ===\n"
    
    # NEW: Add the search snippets so the LLM has baseline data even if scraping fails!
    for res in search_results:
        scraped_context += f"Source: {res['url']}\nSnippet: {res['snippet']}\n\n"

    scraped_context += "=== SCRAPED WEBSITE TEXT ===\n"
    # Scrape the top 2 websites found to gather deeper context
    for i, result in enumerate(search_results[:2]):
        url = result['url']
        print(f"   📄 Attempting to scrape: {url}")
        page_text = scrape_website_text(url)
        
        # Give a little feedback in the terminal on whether the scrape worked
        if len(page_text) < 200 or "Access Denied" in page_text or "Security" in page_text:
             print("   ⚠️ Scrape blocked or minimal text found. Relying on snippets.")
        else:
             print("   ✅ Scrape successful.")
             
        scraped_context += f"\n--- Text from {url} ---\n{page_text}\n"

    # 2. Prepare the prompt for the LLM
    prompt = f"""
    You are an expert business researcher. Analyze the following web search snippets and website text for the company '{company_name}' located in '{location}'.
    
    Extract the following information:
    1. What the business does (Summary)
    2. Size signals (Are they small, enterprise, number of locations, etc.)
    3. Digital presence (Do they have a modern site, active socials, directories?)
    4. Tools/Systems used (Do they use a CRM, booking system, or mention specific tech?)
    
    Synthesize the data intelligently. Even if you only have a short snippet, infer what you can logically. 
    If information for a specific field is completely absent from all text, write "Not publicly available". Do not hallucinate.
    
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
                response_schema=BusinessProfile,
                temperature=0.2 
            ),
        )
        
        print("✅ [Agent 01] Research complete.")
        import json
        return json.loads(response.text)
        
    except Exception as e:
        print(f"❌ [Agent 01] LLM Error: {e}")
        return None

if __name__ == "__main__":
    # Testing a highly specific company name
    test_profile = run_researcher_agent("URJASVINI SOLUTION OPC PRIVATE LIMITED", "RAJASTHAN")
    if test_profile:
        print("\n--- Final Output ---")
        for key, value in test_profile.items():
            print(f"**{key}**: {value}")