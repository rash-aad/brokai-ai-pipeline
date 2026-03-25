import os
from google import genai
from google.genai import types
from pydantic import BaseModel
import json
from dotenv import load_dotenv

load_dotenv()

# The strict output structure for our final message
class OutreachMessage(BaseModel):
    message: str
    platform: str  # e.g., "WhatsApp", "LinkedIn DM", "Email"

def run_outreach_writer_agent(company_name, business_profile, contact_card):
    """Agent 03: Generates a highly personalized cold outreach message."""
    print(f"\n✍️  [Agent 03] Drafting outreach for: {company_name}...")
    
    # --- THE SAFETY NET ---
    # If Agent 01 failed, give Agent 03 an empty dictionary so it doesn't crash
    if business_profile is None:
        business_profile = {}
        
    # If Agent 02 failed, assume no contact info was found
    if contact_card is None:
        contact_card = {
            "contact_found": False, 
            "email": "Not publicly available", 
            "phone": "Not publicly available", 
            "whatsapp": "Not publicly available"
        }

    # 1. Determine the best platform based on our extracted contact data
    platform_context = ""
    if contact_card.get("whatsapp") != "Not publicly available" or contact_card.get("phone") != "Not publicly available":
        platform_context = "Write this as a short, punchy WhatsApp message."
    elif contact_card.get("email") != "Not publicly available":
        platform_context = "Write this as a short, direct cold Email."
    else:
        platform_context = "Write this as a short LinkedIn DM since we could not find their direct contact info."

        
    # 2. Prepare the prompt with the outputs from Agents 1 & 2
    prompt = f"""
    You are an elite sales copywriter working for Brokai Labs. 
    Brokai Labs builds AI-powered systems for small and medium businesses (AI voice receptionists, field operations SaaS, and communication automation).
    
    Write a cold outreach message to: {company_name}
    
    {platform_context}
    
    Use this research to personalize the message:
    - What they do: {business_profile.get('summary', 'Unknown')}
    - Size/Age: {business_profile.get('size_signals', 'Unknown')}
    - Tools used: {business_profile.get('tools_used', 'Unknown')}
    
    RULES:
    - Keep it short (under 75 words).
    - Be outcome-first (focus on how Brokai saves them time or gets them leads).
    - Mention one specific thing about their business from the research to prove this isn't spam.
    - DO NOT use generic openings like "I hope this finds you well" or "Dear Sir/Madam".
    - End with a low-friction, casual question.
    """

    # 3. Call the Gemini API
    try:
        client = genai.Client()
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=OutreachMessage,
                # We use a slightly higher temperature (0.7) here so the AI can be creative with its copywriting
                temperature=0.7 
            ),
        )
        
        print("✅ [Agent 03] Message drafted.")
        return json.loads(response.text)
        
    except Exception as e:
        print(f"❌ [Agent 03] LLM Error: {e}")
        return None

# --- Quick Test Block ---
if __name__ == "__main__":
    # We will use the exact data we successfully extracted for Urjasvini!
    mock_profile = {
        "summary": "Specializes in transformer maintenance and filtration, along with all types of electrification services.",
        "size_signals": "9 years old, private company.",
        "tools_used": "Not publicly available"
    }
    
    # Passing in the real contact data we just fought so hard to get
    mock_contact = {
        "contact_found": True,
        "phone": "8493654723, 9001473333",
        "email": "namanjain@urjasvinisolutions.com",
        "whatsapp": "Not publicly available"
    }
    
    test_message = run_outreach_writer_agent("URJASVINI SOLUTION OPC PRIVATE LIMITED", mock_profile, mock_contact)
    if test_message:
        print(f"\n--- Final Outreach Message ({test_message['platform']}) ---")
        print(test_message['message'])