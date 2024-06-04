from flask import Flask, request, session, jsonify, send_from_directory, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit
import os
import time
from shared_memory_manager import SharedMemoryManager
from werkzeug.utils import secure_filename

app = Flask(__name__, static_url_path='/templates', static_folder='templates')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_PATH'] = 1000000
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'

db = SQLAlchemy(app)
shared_memory_manager = SharedMemoryManager()
socketio = SocketIO(app, async_mode='threading')

# Si la carpeta no existe, se crea.
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Modelo para el Usuario.
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f"User('{self.username}')"

# Para poder guardar los mensajes del chat y que no se pierdan.
chat_messages = [] 
# Usuarios conectados
connected_users = set()

# Ruta para index.
@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html')
    else:
        return redirect(url_for('login'))

# Ruta para login. Se verifica que exista el usuario y redirige al index.
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['username'] = username
            return redirect(url_for('index'))
    return render_template('login.html')


# Ruta para register. Se guarda el username y la password en la bd.
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        session['username'] = username
        return redirect(url_for('index'))
    return render_template('register.html')

# Ruta para cargar archivos
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
    
# Ruta para mostrar los archivos
@app.route('/files', methods=['GET'])
def list_files():
    files = shared_memory_manager.get_results()
    return jsonify(files)

# Ruta para descargar archivos
@app.route('/uploads/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Ruta para logout.
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Manejar mensajes del chat. 
@socketio.on('message')
def handle_message(data):
    username = data['username']
    message = data['message']
    chat_messages.append({'username': username, 'message': message})
    emit('message', {'username': username, 'message': message}, broadcast=True)

# Manejar la conexión del cliente al servidor. El sv envia todos los mensajes anteriores al cliente.
@socketio.on('connect')
def handle_connect():
    username = session.get('username')
    if username:
        connected_users.add(username)
        emit('user_connected', {'username': username}, broadcast=True)
        emit('connected_users', list(connected_users), broadcast=True)
    
    for message in chat_messages:
        emit('message', {'username': message['username'], 'message': message['message']})

@socketio.on('disconnect')
def handle_disconnect():
    username = session.get('username')
    if username and username in connected_users:
        connected_users.remove(username)
        emit('user_disconnected', {'username': username}, broadcast=True)
        emit('connected_users', list(connected_users), broadcast=True)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, host='::', port=5000, debug=True)
