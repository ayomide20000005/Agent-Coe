import streamlit as st
from PIL import Image
import easyocr

st.set_page_config(page_title="Agent Coe", page_icon="🤖")
st.title("🤖 Agent Coe: Document Validator")

# --- CONFIGURATION SWITCH ---
# Set this to True when you are ready to activate text extraction
OCR_ENABLED = False 

st.write("Upload a document to validate its content.")

uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption='Uploaded Document', use_container_width=True)
    
    if OCR_ENABLED:
        st.info("⏳ Processing text... (First run may take 30s)")
        try:
            # Initialize reader only when enabled
            reader = easyocr.Reader(['en'], gpu=False)
            results = reader.readtext(image)
            text = " ".join([result[1] for result in results])
            
            if text.strip():
                st.success("✅ Text Extracted!")
                st.text_area("Extracted Content", value=text, height=200)
            else:
                st.warning("No text detected.")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.info("🚧 **OCR Interface Active but Paused.**\n\nThe system is ready. To start extracting text, set `OCR_ENABLED = True` in the code and redeploy.")
        st.success("✅ Image Uploaded Successfully")
else:
    st.info("👆 Please upload an image to begin.")
