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

def get_download_url(file_id):
    """Get the shareable URL for the file download page"""
    app_url = st.secrets["app_url"]  # Ensure this exists in `.streamlit/secrets.toml`
    return f"{app_url}?file_id={file_id}"

# Clean expired files
clean_expired_files()

# Page Header
st.title("File to QR Code Sharing")

# Check if we're in download mode
params = st.experimental_get_query_params()
if "file_id" in params:
    file_id = params["file_id"][0]
    file_path = os.path.join(UPLOAD_DIR, file_id)

    if os.path.exists(file_path):
        filename = file_id.split("_", 1)[1]  # Extract original filename

        st.success(f"File found: {filename}")

        col1, col2 = st.columns(2)
        with col1:
            with open(file_path, "rb") as f:
                st.download_button(
                    label="Download File",
                    data=f,
                    file_name=filename,
                    mime="application/octet-stream"
                )
        with col2:
            created_time = os.path.getctime(file_path)
            time_left = int(FILE_EXPIRY - (time.time() - created_time) / 60)
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
        # Store file persistently
        file_id = f"{uuid.uuid4()}_{uploaded_file.name}"
        file_path = os.path.join(UPLOAD_DIR, file_id)

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getvalue())

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
