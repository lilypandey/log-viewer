import time
import threading
from collections import deque

class LogWatcher:
    def __init__(self, filepath, buffer_size=10):
        self.filepath = filepath
        self.buffer_size = buffer_size
        self.queue = deque(maxlen=buffer_size)
        self.lock = threading.Lock()
        self.clients = []
        self.last_position = 0
        self.client_callbacks = {}
        self._initialize_queue()

        thread = threading.Thread(target=self._watch_log_file, daemon=True)
        thread.start()

    def _initialize_queue(self):
         with open(self.filepath, 'rb') as f:
             f.seek(0, 2)
             filesize = f.tell()
             block_size = 1024
             blocks = []
 
             while  filesize>0 and len(self.queue) < self.buffer_size:
                 f.seek(max(filesize - block_size,0))
                 data = f.read(block_size)
                 blocks.append(data)
                 filesize -= block_size
                 lines = b''.join(reversed(blocks)).decode(errors='ignore').splitlines()
                 self.queue = deque(lines[-self.buffer_size:], maxlen=self.buffer_size)
             f.seek(0,2)
             self.last_position = f.tell()

    def _watch_log_file(self):
        while True:
            time.sleep(1)
            with open(self.filepath, 'r') as f:
                f.seek(self.last_position)
                new_lines = f.readlines()
                if new_lines:
                    new_lines = [line.strip() for line in new_lines if line.strip()]
                    with self.lock:
                        self.queue.extend(new_lines)
                        for callback in self.clients:
                            callback(new_lines)
                self.last_position = f.tell()

    def register_client_with_snapshot(self, callback):
        with self.lock:
            snapshot = list(self.queue)
            self.clients.append(callback)
            return snapshot
        
    def unregister_client(self, callback): 
        with self.lock:
            if callback in self.clients:
                self.clients.remove(callback)