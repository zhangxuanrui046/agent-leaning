import glob, json, time
from pathlib import Path

_counter = None


def _get_next_seq(log_dir: str) -> int:
    global _counter
    if _counter is not None:
        _counter += 1
        return _counter

    # 首次调用：扫描 today 的日志文件，取最大序号 + 1
    today = time.strftime("%Y%m%d")
    pattern = str(Path(log_dir) / f"traj_{today}-*-*.jsonl")
    max_seq = 0
    for f in glob.glob(pattern):
        name = Path(f).stem
        parts = name.split("-")
        if len(parts) >= 3:
            try:
                max_seq = max(max_seq, int(parts[-1]))
            except ValueError:
                pass
    _counter = max_seq + 1
    return _counter


def init_run(log_dir="logs"):
    ts = time.strftime("%Y%m%d-%H%M%S")
    seq = _get_next_seq(log_dir)
    run_id = f"{ts}-{seq}"
    log_path = Path(log_dir) / f"traj_{run_id}.jsonl"
    log_path.parent.mkdir(exist_ok=True)
    return run_id, str(log_path)


def log_event(log_path, **kwargs):
    entry = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), **kwargs}
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
