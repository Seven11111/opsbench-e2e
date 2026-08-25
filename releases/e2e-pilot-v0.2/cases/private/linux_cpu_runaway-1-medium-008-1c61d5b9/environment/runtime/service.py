import json
import time
from pathlib import Path

runtime = Path(__file__).parent
while True:
    config = json.loads((runtime / "config.json").read_text())
    runaway = bool(config["runaway"])
    (runtime / "status.json").write_text(json.dumps({"healthy": not runaway, "runaway": runaway}))
    if runaway:
        sum(index * index for index in range(50000))
    else:
        time.sleep(1)
