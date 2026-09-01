from pathlib import Path
import subprocess

root = Path(__file__).parents[1]
path = root / 'environment/runtime/fluent-bit.conf'
path.write_text(path.read_text().replace('Host         sink', 'Host         missing-sink'), encoding='utf-8')
subprocess.run(['curl', '-fsS', '-X', 'POST', '-d', '{}', 'http://127.0.0.1:19202/api/v2/reload'], check=True)
