from flask import Flask, request, session, jsonify, send_from_directory, render_template
from werkzeug.utils import secure_filename
import os
import time
from shared_memory_manager import SharedMemoryManager

app = Flask(__name__, static_url_path='/templates', static_folder='templates')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_PATH'] = 1000000

shared_memory_manager = SharedMemoryManager()

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        uploader = session.get('username', 'Anónimo')
        file_info = {
            'timestamp': time.time(),
            'uploader': uploader
        }
        shared_memory_manager.update_result(filename, file_info)
        return jsonify({'success': True, 'filename': filename}), 201

@app.route('/files', methods=['GET'])
def list_files():
    files = shared_memory_manager.get_results()
    return jsonify(files)

@app.route('/uploads/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
