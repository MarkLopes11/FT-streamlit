from flask import Flask, request, render_template, send_from_directory, url_for, redirect
import qrcode
from werkzeug.utils import secure_filename
import os
import uuid
import time
import socket
from threading import Thread

# Get the local IP address of the machine
def get_local_ip():
    try:
        # Create a socket connection to an external server
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# Get the local IP address
LOCAL_IP = get_local_ip()
PORT = 5000
BASE_URL = f"http://{LOCAL_IP}:{PORT}"

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
QR_FOLDER = 'static/qrcodes'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'zip'}
FILE_EXPIRY = 3600  # Files expire after 1 hour (in seconds)

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)
os.makedirs('static', exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['QR_FOLDER'] = QR_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_qr_code(url, qr_path):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(qr_path)
    return qr_path

def cleanup_old_files():
    """Remove files that are older than FILE_EXPIRY seconds"""
    while True:
        current_time = time.time()
        # Check uploads folder
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(file_path) and (current_time - os.path.getmtime(file_path)) > FILE_EXPIRY:
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error removing file {file_path}: {e}")
        
        # Check QR codes folder
        for filename in os.listdir(QR_FOLDER):
            file_path = os.path.join(QR_FOLDER, filename)
            if os.path.isfile(file_path) and (current_time - os.path.getmtime(file_path)) > FILE_EXPIRY:
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error removing QR code {file_path}: {e}")
                
        time.sleep(300)  # Check every 5 minutes

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'GET':
        # If someone navigates to /upload directly, redirect them to the home page
        return redirect(url_for('index'))
    
    if 'file' not in request.files:
        return render_template('index.html', error='No file part')
    
    file = request.files['file']
    
    if file.filename == '':
        return render_template('index.html', error='No selected file')
    
    if file and allowed_file(file.filename):
        try:
            # Generate unique filename
            original_filename = secure_filename(file.filename)
            unique_id = str(uuid.uuid4())
            filename = f"{unique_id}_{original_filename}"
            
            # Save the uploaded file
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Generate direct download URL using the local IP address instead of localhost
            download_url = f"{BASE_URL}/download/{filename}"
            
            # Generate QR code
            qr_filename = f"{unique_id}.png"
            qr_path = os.path.join(app.config['QR_FOLDER'], qr_filename)
            generate_qr_code(download_url, qr_path)
            
            # Get server IP for display
            server_ip = LOCAL_IP
            
            # Return the result page with the QR code
            return render_template(
                'result.html',
                qr_code=f"/static/qrcodes/{qr_filename}",
                filename=original_filename,
                download_url=download_url,
                expiry_time=FILE_EXPIRY//60,  # Convert to minutes
                server_ip=server_ip
            )
        except Exception as e:
            # Log the error and return a user-friendly message
            print(f"Error processing file: {e}")
            return render_template('index.html', error=f'An error occurred while processing your file: {str(e)}')
    
    return render_template('index.html', error='File type not allowed')

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    # Print information about the server
    print(f"=" * 50)
    print(f"Server running on: {LOCAL_IP}:{PORT}")
    print(f"Access the application at: {BASE_URL}")
    print(f"=" * 50)
    
    # Start cleanup thread
    cleanup_thread = Thread(target=cleanup_old_files, daemon=True)
    cleanup_thread.start()
    
    # Run the app
    app.run(host='0.0.0.0', port=PORT, debug=True)