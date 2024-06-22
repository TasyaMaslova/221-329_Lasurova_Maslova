from flask import Flask, request, jsonify
import os
import subprocess
import logging 
import threading
from pywinauto import Application, timings

app = Flask(__name__)

UPLOAD_FOLDER = 'C:/Users/Shiro/Desktop/passThrough'  
ALLOWED_EXTENSIONS = {'inf', 'sys', 'cat'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def clear_upload_folder():
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
            logger.info(f'Removed old file: {file_path}')

@app.route('/clear', methods=['POST'])
def clear_folder():
    clear_upload_folder()
    return jsonify({'message': 'Upload folder cleared'}), 200

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        logger.error('No file part in the request')
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        logger.error('No selected file')
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        logger.info(f'File {file.filename} successfully uploaded to {filepath}')
        return jsonify({'message': 'File successfully uploaded'}), 200
    logger.error('File not allowed')
    return jsonify({'error': 'File not allowed'}), 400

def handle_installation_popup():
    try:
        logger.info('Waiting for the Windows Security popup to appear...')
        timings.wait_until_passes(15, 1, lambda: Application(backend="uia").connect(title_re="Безопасность Windows"))
        app = Application(backend="uia").connect(title_re="Безопасность Windows")
        dlg = app.window(title_re="Безопасность Windows")
        logger.info('Windows Security window found, attempting to click the button...')

        button = dlg.child_window(title="Все равно установить этот драйвер", control_type="Button")
        if button.exists(timeout=10):
            logger.info('Button found, clicking...')
            button.click()
        else:
            logger.error('Button not found within the window.')
        
        logger.info('Handled driver installation popup')
    except Exception as e:
        logger.error(f'Failed to handle installation popup: {e}')

def install_driver_thread(inf_file):
    cmd = f'pnputil /add-driver "{inf_file}" /install'
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if result.returncode == 0:
        logger.info('Driver successfully installed')
        load_driver()
    else:
        logger.error(f'Failed to install driver: {result.stderr}')

def load_driver():
    try:
        cmd = "fltmc load PassThrough"
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            logger.info('Driver successfully loaded')
        else:
            logger.error(f'Failed to load driver: {result.stderr}')
    except Exception as e:
        logger.error(f'Failed to execute load driver command: {e}')

@app.route('/install', methods=['POST'])
def install_driver():
    files_to_check = ['passThrough.inf', 'passThrough.sys', 'passthrough.cat']
    missing_files = [file for file in files_to_check if not os.path.exists(os.path.join(UPLOAD_FOLDER, file))]
    
    if missing_files:
        logger.error(f'Files not found: {", ".join(missing_files)}')
        return jsonify({'error': f'Files not found: {", ".join(missing_files)}'}), 400

    inf_file = os.path.join(UPLOAD_FOLDER, 'passThrough.inf')
    if not os.path.exists(inf_file):
        logger.error('INF file not found')
        return jsonify({'error': 'INF file not found'}), 400
    
    popup_thread = threading.Thread(target=handle_installation_popup)
    popup_thread.start()

    install_driver_thread(inf_file)

    popup_thread.join()

    return jsonify({'message': 'Driver installation process completed'}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)