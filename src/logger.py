import random,string,json,time
from pathlib import Path

_current_run_id = None
def init_run(log_dir = "logs"):
    global _current_run_id
    ts = time.strftime("%Y%m%d-%H%M%S")
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits,k = 4))
    run_id = f"{ts}-{suffix}"
    log_path = Path(log_dir) / f"traj_{run_id}.jsonl"
    log_path.parent.mkdir(exist_ok = True)
    _current_run_id = run_id
    return run_id,str(log_path)

def log_event(log_path, **kwargs):
    entry = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "run_id": _current_run_id, **kwargs}
    with open(log_path,"a",encoding= "utf-8") as f:
        f.write(json.dumps(entry,ensure_ascii = False)+"\n")

    
