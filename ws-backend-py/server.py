from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/')
def index():
    return "Servidor de WebSockets con Flask-SocketIO está en funcionamiento"

@socketio.on('connect')
def handle_connect():
    client_id = request.sid
    print(f"Client connected with ID: {client_id}")

@socketio.on('transcription')
def handle_message(data):
    client_id = request.sid
    print(f"Received transcription from {client_id}: {data}")
    # Aquí puedes procesar el mensaje como necesites
    processed_data = data.upper()  # Ejemplo de procesamiento simple
    print(f"Processed transcription: {processed_data}")

@socketio.on('disconnect')
def handle_disconnect():
    client_id = request.sid
    print(f"Client disconnected with ID: {client_id}")

if __name__ == '__main__':
    socketio.run(app, debug=True, port=3000)