import streamlit as st
import qrcode
from io import BytesIO
import uuid
import time
import os

st.set_page_config(page_title="File to QR Code Sharing", layout="centered")

# Constants
FILE_EXPIRY = 60  # minutes
UPLOAD_DIR = "uploaded_files"  # Directory to store uploaded files

# Ensure upload directory exists
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def clean_expired_files():
    """Remove expired files from storage"""
    current_time = time.time()
    for filename in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.isfile(file_path):
            created_time = os.path.getctime(file_path)
            if current_time - created_time > FILE_EXPIRY * 60:
                os.remove(file_path)

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

def get_direct_download_url(file_id):
    """Return a direct file download URL"""
    app_url = st.secrets["app_url"]  # Ensure this exists in `.streamlit/secrets.toml`
    return f"{app_url}?file_id={file_id}&download=true"

# Clean expired files
clean_expired_files()

# Get URL parameters
params = st.query_params()

if "file_id" in params and "download" in params:
    # Directly serve the file for download
    file_id = params["file_id"][0]
    file_path = os.path.join(UPLOAD_DIR, file_id)

    if os.path.exists(file_path):
        filename = file_id.split("_", 1)[1]  # Extract original filename
        with open(file_path, "rb") as f:
            st.download_button(label="Download File", data=f, file_name=filename, mime="application/octet-stream", key="auto_download", use_container_width=True)
    else:
        st.error("File not found or has expired")
else:
    # Main Upload Interface
    st.title("File to QR Code Sharing")
    st.info("Upload any file and get a QR code to **directly download** the file when scanned.")
    st.warning(f"Files are automatically deleted after {FILE_EXPIRY} minutes.")

    uploaded_file = st.file_uploader("Choose a file", type=None)

    if uploaded_file is not None:
        # Store file persistently
        file_id = f"{uuid.uuid4()}_{uploaded_file.name}"
        file_path = os.path.join(UPLOAD_DIR, file_id)

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getvalue())

        direct_download_url = get_direct_download_url(file_id)

        # Display QR code
        st.subheader("Scan to Download Instantly!")
        qr_image = generate_qr_code(direct_download_url)
        st.image(qr_image, caption="Scan this QR code to download the file", width=300)

        # Show direct link
        st.subheader("Direct Link")
        st.code(direct_download_url)

        # Important notes
        st.warning(f"This file and QR code will expire after {FILE_EXPIRY} minutes")
