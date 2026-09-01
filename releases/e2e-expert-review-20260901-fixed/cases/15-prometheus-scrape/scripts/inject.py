from pathlib import Path
import subprocess

root = Path(__file__).parents[1]
path = root / 'environment/runtime/prometheus.yml'
path.write_text(path.read_text().replace('exporter:19100', 'missing-exporter:19999'), encoding='utf-8')
subprocess.run(['curl', '-fsS', '-X', 'POST', 'http://127.0.0.1:19090/-/reload'], check=True)
