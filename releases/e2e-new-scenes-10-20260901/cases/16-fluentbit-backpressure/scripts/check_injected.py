from pathlib import Path

if 'Host         missing-sink' not in (Path(__file__).parents[1] / 'environment/runtime/fluent-bit.conf').read_text():
    raise SystemExit('backpressure injection not observed')
