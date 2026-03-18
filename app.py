import streamlit as st
from duckduckgo_search import DDGS
import sqlite3
import os
import pytesseract
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(page_title="Agent Coe", page_icon="🇳🇬", layout="centered")

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

# --- DUCKDUCKGO SEARCH FUNCTION ---
def search_online(query):
    try:
        results = []
        with DDGS() as ddgs:
            # Search for phone + scam keywords
            search_term = f"{query} scam fraud complaint nigeria real estate"
            for r in ddgs.text(search_term, max_results=5):
                results.append(f"🔗 **{r['title']}**: {r['body']}")
        return results
    except Exception as e:
        return [f"⚠️ Search failed (check internet): {str(e)}"]

# --- OCR DOCUMENT FUNCTION ---
def extract_text_from_image(image_file):
    try:
        text = pytesseract.image_to_string(image_file)
        return text
    except Exception as e:
        return f"Error: Tesseract not found or image unreadable. {str(e)}"

# --- MAIN UI ---
st.title("🇳🇬 Agent Coe")
st.markdown("### Verify Agents & Documents for Free")
st.info("No fees. No cards. Just truth.")

tab1, tab2, tab3 = st.tabs(["📞 Check Phone/Agent", "📄 Scan Document", "🚨 Report Scam"])

# TAB 1: PHONE CHECK
with tab1:
    st.header("Check Agent or Landlord Number")
    phone_input = st.text_input("Enter Phone Number (e.g., 08012345678)")
    
    if st.button("Analyze Number"):
        if not phone_input:
            st.warning("Please enter a number.")
        else:
            # 1. Check Local DB
            local_hit = check_local_db(phone_input)
            if local_hit:
                st.error(f"🚨 **ALERT**: This number is in our Scam Database!")
                st.write(f"**Note:** {local_hit[1]}")
            else:
                st.info("✅ Not in local blacklist. Searching online reports...")
                # 2. Search Online
                results = search_online(phone_input)
                if results:
                    st.write("### 🌐 Online Findings:")
                    for res in results:
                        st.markdown(res)
                    st.warning("⚠️ If you see complaints above, proceed with extreme caution.")
                else:
                    st.success("✅ No negative reports found online. Proceed with standard caution.")

# TAB 2: DOCUMENT SCAN
with tab2:
    st.header("Verify Property Documents")
    uploaded_file = st.file_uploader("Upload Photo of Title Deed/Receipt", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded Document", use_column_width=True)
        
        if st.button("Scan Document Text"):
            with st.spinner("Reading document..."):
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

# Footer
st.markdown("---")
st.caption("Built for Nigeria. Runs on free open-source tools.")