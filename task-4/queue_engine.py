import redis
import uuid
import time
import pickle
import importlib
from functools import wraps

# --- Configuration ---
REDIS_CONFIG = {'host': 'localhost', 'port': 6379, 'db': 0}
QUEUE_NAME = 'default'
DLQ_NAME = 'dead_letter'
METADATA_PREFIX = 'task_meta:'
RESULTS_PREFIX = 'result:'

class Task:
    def __init__(self, func_name, args=None, kwargs=None, max_retries=3):
        self.id = str(uuid.uuid4())[:8]
        self.func_name = func_name
        self.args = args or []
        self.kwargs = kwargs or {}
        self.retries = 0
        self.max_retries = max_retries
        self.status = "PENDING"

class DistributedQueue:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = redis.Redis(**REDIS_CONFIG)
        return self._client

    def enqueue(self, func_name, args=None, kwargs=None, max_retries=3):
        task = Task(func_name, args, kwargs, max_retries)
        self._save_metadata(task)
        self.client.rpush(QUEUE_NAME, pickle.dumps(task))
        print(f"Task queued: <Task id={task.id} func={func_name} status=PENDING>")
        return task.id

    def _save_metadata(self, task, duration=None):
        meta = {
            "id": task.id, "func": task.func_name, "status": task.status,
            "retries": str(task.retries), "duration": f"{duration:.2f}s" if duration else "—"
        }
        self.client.hset(f"{METADATA_PREFIX}{task.id}", mapping=meta)

class Worker:
    def __init__(self, worker_id, task_module_name):
        self.id = worker_id
        self.task_module_name = task_module_name
        self.client = None

    def run(self):
        # Create connection and import tasks inside the child process
        self.client = redis.Redis(**REDIS_CONFIG)
        tasks_module = importlib.import_module(self.task_module_name)
        print(f"[WORKER-{self.id}] Started. Monitoring '{QUEUE_NAME}'...")

        while True:
            try:
                _, data = self.client.blpop(QUEUE_NAME)
                task = pickle.loads(data)
                self.process_task(task, tasks_module)
            except Exception as e:
                print(f"[WORKER-{self.id}] Error: {e}")

    def process_task(self, task, tasks_module):
        print(f"[WORKER-{self.id}] Picked up {task.id} ({task.func_name})")
        start_time = time.time()
        try:
            # Look up the function by string name in the imported module
            func = getattr(tasks_module, task.func_name)
            result = func(*task.args, **task.kwargs)
            
            duration = time.time() - start_time
            task.status = "SUCCESS"
            self._update_meta(task, duration)
            print(f"[WORKER-{self.id}] Completed {task.id} in {duration:.2f}s")
        except Exception as e:
            self.handle_failure(task, e)

    def _update_meta(self, task, duration=None):
        meta = {"id": task.id, "func": task.func_name, "status": task.status, 
                "retries": str(task.retries), "duration": f"{duration:.2f}s" if duration else "—"}
        self.client.hset(f"{METADATA_PREFIX}{task.id}", mapping=meta)

    def handle_failure(self, task, error):
        if task.retries < task.max_retries:
            task.retries += 1
            delay = 2 ** task.retries
            print(f"[WORKER-{self.id}] {task.id} FAILED ({type(error).__name__}) - Retry {task.retries} in {delay}s")
            time.sleep(delay)
            self.client.rpush(QUEUE_NAME, pickle.dumps(task))
        else:
            task.status = "DEAD_LETTER"
            self._update_meta(task)
            self.client.rpush(DLQ_NAME, pickle.dumps(task))
            print(f"[WORKER-{self.id}] {task.id} moved to DLQ")