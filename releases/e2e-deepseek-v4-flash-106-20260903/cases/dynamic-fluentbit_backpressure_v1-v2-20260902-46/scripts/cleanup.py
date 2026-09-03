from pathlib import Path

root = Path(__file__).parents[1]
(root / 'environment/runtime/sink.mode').write_text('healthy\n', encoding='utf-8')
