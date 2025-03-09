import streamlit as st
import qrcode
from io import BytesIO
import uuid
import time
import tempfile
import os
from PIL import Image
import base64

st.set_page_config(page_title="File to QR Code Sharing", layout="centered")

# Constants
FILE_EXPIRY = 60  # minutes

# Setup session state if not already present
if 'files' not in st.session_state:
    st.session_state.files = {}  # Will store {file_id: {"filename": name, "data": bytes, "created": timestamp}}

# Clean up expired files
current_time = time.time()
files_to_remove = []
for file_id, file_data in st.session_state.files.items():
    if current_time - file_data["created"] > FILE_EXPIRY * 60:
        files_to_remove.append(file_id)
for file_id in files_to_remove:
    del st.session_state.files[file_id]

def generate_qr_code(url):
    """Generate QR code image from URL"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return buffered.getvalue()

def get_download_url(file_id):
    """Get the shareable URL for the file download page"""
    # This assumes your Streamlit app is deployed to Streamlit Cloud
    # You'll need to replace this with your actual deployed URL
    app_url = st.secrets.get("app_url", "https://your-app-url.streamlit.app")
    return f"{app_url}?file_id={file_id}"

# Page Header
st.title("File to QR Code Sharing")

# Check if we're in download mode
params = st.experimental_get_query_params()
if "file_id" in params:
    file_id = params["file_id"][0]
    if file_id in st.session_state.files:
        file_data = st.session_state.files[file_id]
        
        st.success(f"File found: {file_data['filename']}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="Download File",
                data=file_data["data"],
                file_name=file_data["filename"],
                mime="application/octet-stream"
            )
        with col2:
            time_left = int(FILE_EXPIRY - (time.time() - file_data["created"]) / 60)
            st.info(f"File expires in approximately {time_left} minutes")
        
        # Show option to return to upload page
        st.markdown("[⬅️ Back to file upload](./)")
    else:
        st.error("File not found or has expired")
        st.markdown("[⬅️ Back to file upload](./)")
else:
    # Main Upload Interface
    st.info("Upload any file and get a QR code to scan for direct access to the file.")
    st.warning(f"Files are automatically deleted after {FILE_EXPIRY} minutes.")
    
    uploaded_file = st.file_uploader("Choose a file", type=None)
    
    if uploaded_file is not None:
        # Store file data in session state
        file_id = str(uuid.uuid4())
        file_data = uploaded_file.getvalue()
        
        st.session_state.files[file_id] = {
            "filename": uploaded_file.name,
            "data": file_data,
            "created": time.time()
        }
        
        download_url = get_download_url(file_id)
        
        # Display QR code
        st.subheader("Your QR Code is Ready!")
        qr_image = generate_qr_code(download_url)
        st.image(qr_image, caption="Scan this QR code to download the file", width=300)
        
        # Display direct link
        st.subheader("Direct Link")
        st.code(download_url)
        
        # Display important notes
        st.subheader("Important Notes")
        st.info("This link can be accessed from any network or device with internet access")
        st.warning(f"This file and QR code will expire after {FILE_EXPIRY} minutes")