from pathlib import Path

BASE = Path(__file__).parent

with open(Path(BASE, 'test.html'), 'r') as f:
    template = f.read()

icons = [p for p in BASE.iterdir() if p.is_file() and p.name.endswith('.svg')]

images = [f'<img src="{f.name}" />' for f in icons]

with open(Path(BASE, 'test.out.html'), 'w') as f:
    f.write(template.replace("{{icons}}", "\n".join(images)))

    