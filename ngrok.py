import streamlit as st
import qrcode
import webbrowser
from io import BytesIO

# WebTorrent Share URL (Will be generated dynamically)
BASE_URL = "https://instant.io/#"  # WebTorrent-based file sharing

def generate_qr_code(url):
    """Generate QR Code for a given URL"""
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return buffered.getvalue()

st.title("P2P File Transfer via WebTorrent")

uploaded_file = st.file_uploader("Upload a file to share", type=["pdf", "jpg", "png", "zip", "mp4"])

if uploaded_file:
    file_data = uploaded_file.read()
    file_name = uploaded_file.name

    # WebTorrent link for P2P sharing
    share_url = BASE_URL + file_name

    st.write("Scan the QR code below to receive the file:")
    qr_image = generate_qr_code(share_url)
    st.image(qr_image)

    # Open WebTorrent in a browser for the sender
    if st.button("Start Sharing"):
        webbrowser.open(share_url)
