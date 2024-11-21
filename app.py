import os
import shutil
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import atexit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'  # Folder to save uploaded files
socketio = SocketIO(app)

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Function to delete all files in the upload folder
def clear_uploads():
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        shutil.rmtree(app.config['UPLOAD_FOLDER'])
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Recreate the folder

# Register the cleanup function to run at exit
atexit.register(clear_uploads)

@app.route('/')
def index():
    return render_template('main.html')

@app.route('/create_room', methods=['POST'])
def create_room():
    room_id = request.form['room_id']
    return redirect(url_for('room', room_id=room_id))

@app.route('/join_existing_room', methods=['POST'])
def join_existing_room():
    room_id = request.form['room_id']
    return redirect(url_for('room', room_id=room_id))

@app.route('/room/<room_id>')
def room(room_id):
    return render_template('chat_room.html', room_id=room_id)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    room_id = request.form['room_id']

    if file:
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Return the file URL so it can be shared in the chat
        file_url = url_for('uploaded_file', filename=filename, _external=True)
        
        # Notify the room about the new file
        socketio.emit('file_uploaded', {
            'username': request.form.get('username', 'Anonymous'),
            'file_url': file_url,
            'filename': filename
        }, to=room_id)

        return jsonify({'file_url': file_url})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@socketio.on('join')
def handle_join(data):
    room = data['room']
    username = data['username']
    join_room(room)  # Join the specified room
    send(f"{username} has entered the room.", to=room)

@socketio.on('leave')
def handle_leave(data):
    room = data['room']
    username = data['username']
    leave_room(room)
    send(f"{username} has left the room.", to=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    username = data.get('username')  # Use .get() to avoid KeyError if the key is missing
    message = data.get('message')
    
    if username and message:
        # Only send the message if both username and message are present
        send({'username': username, 'message': message}, to=room)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
