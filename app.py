from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, send

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('main.html')

@app.route('/create_room', methods=['POST'])
def create_room():
    room_id = request.form['room_id']
    return redirect(url_for('room', room_id=room_id))

# Renamed this route to avoid conflict with the `join_room` function from `flask_socketio`
@app.route('/join_existing_room', methods=['POST'])
def join_existing_room():
    room_id = request.form['room_id']
    return redirect(url_for('room', room_id=room_id))

@app.route('/room/<room_id>')
def room(room_id):
    return render_template('chat_room.html', room_id=room_id)

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
    socketio.run(app, allow_unsafe_werkzeug=True)
