import streamlit as st
from ddgs import DDGS
import os
import pytesseract
from PIL import Image
import time
import hashlib
import re
import platform
import shutil

# --- SMART TESSERACT CONFIGURATION ---
# Automatically detects OS and sets the correct path
system_os = platform.system()

if system_os == "Windows":
    # Your local Windows path
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
else:
    # Linux/Mac (Streamlit Cloud) - relies on system installation
    # Check if tesseract is in PATH, otherwise try common linux paths
    if shutil.which("tesseract") is None:
        # Fallback for some linux environments if not in PATH
        pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# --- CONFIGURATION ---
st.set_page_config(page_title="Agent Coe", page_icon="🛡️", layout="wide")

# Ensure uploads folder exists
if not os.path.exists('uploads'):
    os.makedirs('uploads')

# --- ADVANCED SEARCH FUNCTION ---
def search_online(query):
    try:
        results = []
        if not query:
            return []
        
        with DDGS() as ddgs:
            generator = ddgs.text(f'{query} dispute fraud scam ownership conflict', max_results=5)
            for r in generator:
                if r and 'title' in r and 'body' in r and 'href' in r:
                    results.append({
                        "title": r['title'],
                        "link": r['href'],
                        "snippet": r['body']
                    })
        return results
    except Exception as e:
        return [{"title": "Search Error", "link": "#", "snippet": f"Connection failed: {str(e)}"}]

# --- FIXED OCR DOCUMENT FUNCTION ---
def extract_text_from_image(image_file):
    try:
        img = Image.open(image_file)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        return f"ERROR: {str(e)}"

# --- SHA-256 HASHING FUNCTION ---
def generate_file_hash(file_bytes):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(file_bytes)
    return sha256_hash.hexdigest()

# --- VERIFICATION LOGIC ENGINE ---
def calculate_verification_level(text, web_results):
    score = 100
    reasons = []
    level = "🟢 VERIFIED"
    color = "green"

    # 1. Check Text Clarity
    if len(text) < 50:
        score -= 40
        reasons.append("Low text clarity (Document may be blurry or incomplete).")
    
    # 2. Check Internal Keywords
    bad_keywords = ["forged", "cancelled", "litigation", "acquisition", "dispute", "revoked", "fake", "void"]
    found_flags = [word for word in bad_keywords if word in text.lower()]
    
    if found_flags:
        score -= 50
        reasons.append(f"Critical keywords detected: {', '.join(found_flags)}.")
        level = "🔴 HIGH RISK"
        color = "red"

    # 3. Check Web Corroboration
    if web_results:
        score -= 40
        reasons.append(f"Web search found {len(web_results)} potential conflict reports.")
        level = "🔴 HIGH RISK"
        color = "red"
    else:
        if score == 100:
            level = "🟡 UNCONFIRMED"
            color = "orange"
            reasons.append("No negative reports found, but no independent public verification yet.")
        elif score > 60:
            level = "🟡 UNCONFIRMED"
            color = "orange"
            reasons.append("Minor issues detected; physical verification recommended.")

    if score <= 40:
        level = "🔴 HIGH RISK"
        color = "red"
    
    return level, color, score, reasons

# --- MAIN UI ---
st.title("Agent Coe")
st.markdown("### Direct Evidence Search & Document Verification")
st.info("Upload docs to get a **Verification Level**, digital fingerprint, and auto-investigation.")

tab1, tab2 = st.tabs(["🔍 Deep Web Search", "📄 Scan & Investigate Document"])

# TAB 1: DEEP WEB SEARCH
with tab1:
    st.header("Find Direct Evidence Online")
    
    col1, col2 = st.columns(2)
    with col1:
        inp_phone = st.text_input("Phone Number")
        inp_name = st.text_input("Name")
    with col2:
        inp_city = st.text_input("City/Location")
        inp_desc = st.text_input("Keywords (e.g., stole deposit)")
    
    if st.button("Search Web Now", type="primary"):
        if not any([inp_phone, inp_name, inp_city, inp_desc]):
            st.warning("Please enter at least one detail.")
        else:
            parts = []
            if inp_phone: parts.append(f'"{inp_phone}"')
            if inp_name: parts.append(f'"{inp_name}"')
            if inp_city: parts.append(f'"{inp_city}"')
            if inp_desc: parts.append(f'"{inp_desc}"')
            
            final_query = " AND ".join(parts)

            with st.spinner(""):
                time.sleep(0.5) 
                results = search_online(final_query)
            
            if not results:
                st.warning("⚠️ No direct web pages found containing this combination.")
            else:
                st.success(f"Found {len(results)} matches:")
                st.divider()
                for res in results:
                    with st.container():
                        st.markdown(f"#### [{res['title']}]({res['link']})")
                        st.caption(f"Source: {res['link']}")
                        st.write(f"**Snippet:** _{res['snippet']}_")
                        st.markdown("---")

# TAB 2: SCAN & INVESTIGATE
with tab2:
    st.header("Verify Property Documents")
    st.markdown("Upload a document to receive a **System Integrity Score** and **Verification Level**.")
    
    uploaded_file = st.file_uploader("Upload Photo (JPG/PNG)", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded Document", use_container_width=True)
        
        file_bytes = uploaded_file.getvalue()
        file_hash = generate_file_hash(file_bytes)
        
        st.success(f"✅ **Digital Fingerprint (SHA-256):** `{file_hash}`")
        st.caption("Save this hash. Any alteration to this image will change the fingerprint completely.")
        st.divider()
        
        if st.button("Scan & Calculate Verification Level", type="primary"):
            with st.spinner("📄 Analyzing text, hashing, and cross-referencing web..."):
                text = extract_text_from_image(uploaded_file)
                
                if text is None or text.startswith("ERROR"):
                    st.error(f"❌ **Scan Failed**: {text if text.startswith('ERROR') else 'Could not extract text.'}")
                else:
                    lines = text.split('\n')
                    potential_queries = []
                    for line in lines:
                        line = line.strip()
                        if 5 < len(line) < 60: 
                            if not any(word in line.lower() for word in ["the", "and", "for", "whereas", "thereof", "this", "that"]):
                                potential_queries.append(line)
                    
                    unique_queries = list(dict.fromkeys(potential_queries))[:3]
                    
                    all_web_results = []
                    if unique_queries:
                        for q in unique_queries:
                            res = search_online(q)
                            if res:
                                all_web_results.extend(res)
                    
                    level, color, score, reasons = calculate_verification_level(text, all_web_results)
                    
                    st.divider()
                    st.subheader("🛡️ System Integrity Report")
                    
                    if color == "green":
                        st.success(f"# {level} (Score: {score}/100)")
                    elif color == "orange":
                        st.warning(f"# {level} (Score: {score}/100)")
                    else:
                        st.error(f"# {level} (Score: {score}/100)")
                    
                    if reasons:
                        st.markdown("**Analysis Details:**")
                        for reason in reasons:
                            st.write(f"- {reason}")
                    
                    st.divider()
                    
                    with st.expander("View Extracted Text & Raw Data"):
                        st.text_area("Content", text, height=150)
                        if all_web_results:
                            st.markdown("**⚠️ Conflicting Web Evidence Found:**")
                            for res in all_web_results:
                                st.markdown(f"- [{res['title']}]({res['link']})")
                                st.caption(f"_{res['snippet']}_")
                        else:
                            st.info("No conflicting web evidence found for extracted details.")