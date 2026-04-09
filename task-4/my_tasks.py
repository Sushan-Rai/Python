import time
import os

def generate_thumbnail(image_id, size):
    time.sleep(1)
    return f"/thumbs/{image_id}_{size[0]}x{size[1]}.jpg"

def send_email(to, template):
    attempts_file = f"attempts_{to}.txt"
    attempts = 0
    if os.path.exists(attempts_file):
        with open(attempts_file, "r") as f: attempts = int(f.read())
    
    if attempts < 2:
        with open(attempts_file, "w") as f: f.write(str(attempts + 1))
        raise ConnectionError("SMTP Server Busy")
    
    if os.path.exists(attempts_file): os.remove(attempts_file)
    return "sent"

def generate_report(user_id):
    raise ValueError("DB Timeout")