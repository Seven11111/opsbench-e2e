import json
import multiprocessing
import time
from pathlib import Path

runtime = Path("/runtime")

def consume_cpu(work_units):
    while True:
        sum(index * index for index in range(work_units))

worker = None
while True:
    config = json.loads((runtime / "config.json").read_text())
    runaway = bool(config["runaway"])
    work_units = int(config.get("work_units", 50000))
    if runaway:
        if worker is None or not worker.is_alive():
            worker = multiprocessing.Process(target=consume_cpu, args=(work_units,), daemon=True)
            worker.start()
    elif worker is not None:
        worker.terminate()
        worker.join(timeout=2)
        worker = None
    (runtime / "status.json").write_text(json.dumps({"healthy": not runaway, "runaway": runaway}))
    time.sleep(0.5)
