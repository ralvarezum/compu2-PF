import json
from multiprocessing import Lock
from multiprocessing import shared_memory as shm

class SharedMemoryManager:
    def __init__(self):
        self.shared_memory = shm.SharedMemory(create=True, size=1024)
        self.data = {}
        self.read_lock = Lock()
        self.write_lock = Lock()
        self.shared_memory.buf[0:len(json.dumps(self.data))] = json.dumps(self.data).encode()

    def update_result(self, filename, info):
        with self.write_lock:
            previous_data = self.get_results()
            previous_data[filename] = info
            json_string = json.dumps(previous_data)
            self.shared_memory.buf[0:len(json_string)] = json_string.encode()

    def get_results(self):
        with self.read_lock:
            json_data = self.shared_memory.buf[:].tobytes().decode().strip('\x00')
            return json.loads(json_data)

    def clear_results(self):
        with self.write_lock:
            self.shared_memory.buf[:self.shared_memory.size] = b'\x00' * self.shared_memory.size
            self.data = {}
            self.shared_memory.buf[0:len(json.dumps(self.data))] = json.dumps(self.data).encode()
