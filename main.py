import streamlit as st
import pandas as pd
import os
import time
from agents.researcher import run_researcher_agent
from agents.contact_finder import run_contact_finder_agent
from agents.outreach_writer import run_outreach_writer_agent

# --- Streamlit Page Setup ---
st.set_page_config(page_title="Brokai Lead Gen AI", page_icon="🤖", layout="wide")
st.title("🤖 Brokai Labs: AI Lead Intelligence Pipeline")

# --- Data Loading ---
@st.cache_data
def load_data():
    file_path = "data/Rajasthan Solar leadlist.xlsx"
    if not os.path.exists(file_path):
        return []
    df = pd.read_excel(file_path)
    # Extracting Name and Location based on our earlier fix
    extracted = df.iloc[:, [3, 2]].copy()
    extracted.columns = ['name', 'location']
    extracted = extracted.dropna(subset=['name'])
    extracted['location'] = extracted['location'].fillna("Location not specified")
    return extracted.to_dict('records')

companies = load_data()

if not companies:
    st.error("❌ Could not load the lead list. Check the data folder.")
    st.stop()

# --- State Management ---
# This keeps track of which company we are currently viewing
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0

# --- Sidebar UI ---
st.sidebar.header("Pipeline Controls")
st.sidebar.write(f"**Total Leads Loaded:** {len(companies)}")
st.sidebar.write(f"**Current Lead Index:** {st.session_state.current_index + 1}")

if st.sidebar.button("⏭️ Load Next Lead"):
    if st.session_state.current_index < len(companies) - 1:
        st.session_state.current_index += 1
    else:
        st.warning("You have reached the end of the list!")

# --- Main UI ---
current_company = companies[st.session_state.current_index]

st.header(f"🏢 Target: {current_company['name']}")
st.subheader(f"📍 {current_company['location']}")

st.divider()

# --- The Orchestrator Trigger ---
if st.button("🚀 Run Multi-Agent Pipeline", type="primary"):
    
    # Visual progress tracker
    with st.status("Initializing AI Pipeline...", expanded=True) as status:

        time.sleep(8)
        st.write("🕵️‍♂️ **Agent 01:** Researching company profile...")
        profile = run_researcher_agent(current_company['name'], current_company['location'])
        time.sleep(8)
        
        st.write("📞 **Agent 02:** Hunting for contact information...")
        contact = run_contact_finder_agent(current_company['name'], current_company['location'])
        time.sleep(8)
        
        st.write("✍️ **Agent 03:** Drafting personalized outreach...")
        outreach = run_outreach_writer_agent(current_company['name'], profile, contact)
        time.sleep(8)
        
        status.update(label="✅ Pipeline Execution Complete!", state="complete", expanded=False)
    
    # --- Display Results ---
    if profile and contact and outreach:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### 📊 Business Intelligence")
            st.json(profile)
            
            st.write("### 📇 Contact Card")
            if contact['contact_found']:
                st.success("Contact Information Found")
            else:
                st.warning("No public contact info found (Graceful Fallback)")
            st.json(contact)
            
        with col2:
            st.write(f"### 💬 Drafted Message ({outreach['platform']})")
            st.info(outreach['message'])
    else:
        st.error("Pipeline failed to return complete data. Check terminal for errors.")