from flask import Flask, render_template, request
from flask_socketio import SocketIO
from log_reader import LogWatcher

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

log_file_path = 'sample.log'
watcher = LogWatcher(log_file_path)

@socketio.on('connect')
def handle_connect():

    sid = request.sid 
    def push_updates(lines):
        socketio.emit('log_update', {'lines': lines},to = sid)

    snapshot = watcher.register_client_with_snapshot(push_updates)
    socketio.emit('log_update', {'lines': snapshot}, to=sid)

    watcher.client_callbacks[sid] = push_updates

@socketio.on('disconnect')
def handle_disconnect(sid):
    
    callback = watcher.client_callbacks.get(sid)
    if callback:
        watcher.unregister_client(callback)
        del watcher.client_callbacks[sid]

@app.route('/log')
def log_view():
    return render_template('log.html')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)