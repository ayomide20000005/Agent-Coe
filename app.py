import streamlit as st
from ddgs import DDGS
import sqlite3
import os
import pytesseract
from PIL import Image
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Agent Coe", page_icon="🛡️", layout="wide")

# Ensure uploads folder exists
if not os.path.exists('uploads'):
    os.makedirs('uploads')

# --- DATABASE FUNCTIONS ---
def init_db():
    conn = sqlite3.connect('scam_db.sqlite')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS scams
                 (phone TEXT PRIMARY KEY, status TEXT, notes TEXT)''')
    conn.commit()
    conn.close()

def check_local_db(phone):
    if not phone: return None
    conn = sqlite3.connect('scam_db.sqlite')
    c = conn.cursor()
    c.execute("SELECT status, notes FROM scams WHERE phone=?", (phone,))
    result = c.fetchone()
    conn.close()
    return result

def report_scam(phone, notes):
    conn = sqlite3.connect('scam_db.sqlite')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO scams VALUES (?, ?, ?)", (phone, "SCAM", notes))
    conn.commit()
    conn.close()

# Initialize DB
init_db()

# --- ADVANCED SEARCH FUNCTION ---
def search_online(phone, name, city, description):
    try:
        results = []
        
        # Build the query parts based on what user filled
        parts = []
        if phone: parts.append(f'"{phone}"')
        if name: parts.append(f'"{name}"')
        if city: parts.append(f'"{city}"')
        if description: parts.append(f'"{description}"')
        
        if not parts:
            return []

        # Combine parts with AND logic
        final_query = " AND ".join(parts)

        with DDGS() as ddgs:
            # Search for the exact combination
            generator = ddgs.text(final_query, max_results=10)
            
            for r in generator:
                if r and 'title' in r and 'body' in r and 'href' in r:
                    results.append({
                        "title": r['title'],
                        "link": r['href'],
                        "snippet": r['body']
                    })
        
        return results
        
    except Exception as e:
        return [{"title": "Search Error", "link": "#", "snippet": f"Could not connect to web: {str(e)}"}]

# --- OCR DOCUMENT FUNCTION ---
def extract_text_from_image(image_file):
    try:
        text = pytesseract.image_to_string(image_file)
        return text
    except Exception as e:
        return f"Error: Tesseract not found or image unreadable. {str(e)}"

# --- MAIN UI ---
st.title("Agent Coe")
st.markdown("### Direct Evidence Search & Document Verification")
st.info("Enter any detail below. Combine fields for precise results. Click links to verify.")

tab1, tab2, tab3 = st.tabs(["🔍 Deep Web Search", "📄 Scan Document", "🚨 Report Scam"])

# TAB 1: DEEP WEB SEARCH
with tab1:
    st.header("Find Direct Evidence Online")
    st.markdown("Fill one or more fields. The more you fill, the more precise the search.")
    
    col1, col2 = st.columns(2)
    with col1:
        inp_phone = st.text_input("Phone Number (e.g., 08012345678)")
        inp_name = st.text_input("Name (e.g., Mr. Okon)")
    with col2:
        inp_city = st.text_input("City/Location (e.g., Lekki, Abuja)")
        inp_desc = st.text_input("Description/Keywords (e.g., stole deposit, fake title)")
    
    if st.button("Search Web Now", type="primary"):
        if not any([inp_phone, inp_name, inp_city, inp_desc]):
            st.warning("Please enter at least one detail to search.")
        else:
            # Check local DB first if phone is present
            if inp_phone:
                local_hit = check_local_db(inp_phone)
                if local_hit:
                    st.error(f"🚨 **INTERNAL ALERT**: This number is in our Scam Database!")
                    st.write(f"**Note:** {local_hit[1]}")
                    st.divider()

            # SHOW LOADING SPINNER (No text inside)
            with st.spinner(""):
                time.sleep(0.5) 
                results = search_online(inp_phone, inp_name, inp_city, inp_desc)
            
            # Display Results after loading finishes
            if not results:
                st.warning("⚠️ No direct web pages found containing this exact combination of details.")
            else:
                st.success(f"✅ Found {len(results)} direct matches online:")
                st.divider()
                
                for i, res in enumerate(results):
                    # Display as a clean card
                    with st.container():
                        st.markdown(f"#### [{res['title']}]({res['link']})")
                        st.caption(f"Source: {res['link']}")
                        st.write(f"**Snippet:** _{res['snippet']}_")
                        st.markdown("---")

# TAB 2: DOCUMENT SCAN
with tab2:
    st.header("Verify Property Documents")
    uploaded_file = st.file_uploader("Upload Photo of Title Deed/Receipt", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded Document", use_column_width=True)
        
        if st.button("Scan Document Text"):
            with st.spinner("📄 Reading document text..."):
                text = extract_text_from_image(uploaded_file)
                
                st.subheader("Extracted Text:")
                st.text_area("Content", text, height=200)
                
                # Simple Keyword Flagging
                bad_keywords = ["forged", "cancelled", "litigation", "acquisition", "dispute", "revoked", "fake"]
                flags = [word for word in bad_keywords if word in text.lower()]
                
                if flags:
                    st.error(f"🚨 **RED FLAGS DETECTED**: {', '.join(flags)}")
                    st.write("This document contains suspicious keywords. Verify physically.")
                else:
                    st.success("✅ No obvious warning keywords found in text.")
                    st.write("*(Note: This is an automated check. Always verify physically with lands registry.)*")

# TAB 3: REPORT SCAM
with tab3:
    st.header("Help Others: Report a Scammer")
    with st.form("report_form"):
        rep_phone = st.text_input("Scammer's Phone Number")
        rep_note = st.text_area("What happened? (Be specific)")
        submitted = st.form_submit_button("Add to Blacklist")
        
        if submitted:
            if rep_phone and rep_note:
                report_scam(rep_phone, rep_note)
                st.success("✅ Reported! This number is now blocked for all users.")
            else:
                st.warning("Please fill both fields.")

# Footer removed completely