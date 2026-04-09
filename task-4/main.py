import time
import redis
from multiprocessing import Process
from queue_engine import DistributedQueue, Worker, METADATA_PREFIX, REDIS_CONFIG

def show_dashboard():
    client = redis.Redis(**REDIS_CONFIG)
    keys = client.keys(f"{METADATA_PREFIX}*")
    print("\n=== Dashboard ===")
    print(f"{'Task ID':<10} | {'Func':<10} | {'Status':<12} | {'Retries':<7} | {'Duration':<10}")
    print("-" * 60)
    for key in keys:
        m = client.hgetall(key)
        d = {k.decode(): v.decode() for k, v in m.items()}
        print(f"{d['id']:<10} | {d['func']:<10} | {d['status']:<12} | {d['retries']:<7} | {d['duration']:<10}")

if __name__ == "__main__":
    queue = DistributedQueue()
    
    print("=== Broker ===")
    print(f"[BROKER] Listening on redis://localhost:6379/0")

    # 1. Start Workers (Pass the STRING name of the tasks module)
    processes = []
    for i in range(1, 4):
        worker_obj = Worker(worker_id=i, task_module_name="my_tasks")
        p = Process(target=worker_obj.run)
        p.start()
        processes.append(p)

    time.sleep(1)
    print("\n=== Producer ===")
    # 2. Enqueue Tasks by string name
    queue.enqueue("generate_thumbnail", args=[4521, (256, 256)])
    queue.enqueue("send_email", args=["bob@co.com", "welcome"])
    queue.enqueue("generate_report", args=[99], max_retries=2)

    # 3. Wait and View
    try:
        time.sleep(15)
        show_dashboard()
    finally:
        for p in processes:
            p.terminate()
            p.join()