# app.py (Backend)
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import psutil
import time
from threading import Lock
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

thread = None
thread_lock = Lock()

def background_thread():
    while True:
        # Get system metrics
        cpu_percent = psutil.cpu_percent()
        mem_info = psutil.virtual_memory()
        
        # Get process list
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent']):
            processes.append(proc.info)
        
        # Send data to clients
        socketio.emit('system_stats', {
            'cpu': cpu_percent,
            'memory': mem_info.percent,
            'processes': processes
        })
        time.sleep(1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/terminate', methods=['POST'])
def terminate_process():
    pid = int(request.form['pid'])
    try:
        process = psutil.Process(pid)
        process.terminate()
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e))

@socketio.on('connect')
def handle_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)  # Change port