"""Independently parse released Gerber/Excellon and compare drill geometry.
Requires gerbonara; input reports/pcb-geometry.json is exported by KiCad Python.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib, json, math, warnings, zipfile
from gerbonara import LayerStack

root = Path(__file__).resolve().parents[1]
folder = root / 'fabrication/gerbers'
geometry = json.loads((root / 'reports/pcb-geometry.json').read_text())
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter('always')
    stack = LayerStack.open(folder)
parser_warnings = [str(w.message) for w in caught]
expected_layers = {('top', 'copper'), ('bottom', 'copper'), ('top', 'mask'),
                   ('bottom', 'mask'), ('top', 'silk'), ('bottom', 'silk'),
                   ('mechanical', 'outline')}
assert set(stack.graphic_layers) == expected_layers

outline = stack.graphic_layers[('mechanical', 'outline')].objects
ends = Counter()
for item in outline:
    for xy in [(item.x1, item.y1), (item.x2, item.y2)]:
        ends[tuple(round(v, 3) for v in xy)] += 1
assert all(n == 2 for n in ends.values()), 'Open or branched outline'
assert set(ends) == {tuple(round(v, 3) for v in xy) for xy in geometry['outline_vertices']}
size = [max(p[i] for p in ends) - min(p[i] for p in ends) for i in [0, 1]]
assert size == geometry['board_size_mm'] == [100.0, 80.0]
assert geometry['outline_closed'] and geometry['copper_layers'] == 2

actual = []
counts = {}
for plated, drill in [(True, stack.drill_pth), (False, stack.drill_npth)]:
    slots = 0
    for item in drill.objects:
        diameter = item.aperture.diameter
        if hasattr(item, 'x1'):
            slots += 1
            x, y = (item.x1 + item.x2) / 2, (item.y1 + item.y2) / 2
            width = abs(item.x2 - item.x1) + diameter
            height = abs(item.y2 - item.y1) + diameter
            assert min(abs(item.x2-item.x1), abs(item.y2-item.y1)) < 0.001
        else:
            x, y, width, height = item.x, item.y, diameter, diameter
        actual.append((plated, x, y, width, height))
    counts['PTH' if plated else 'NPTH'] = {'round': len(drill.objects)-slots, 'slots': slots}

unmatched = actual.copy()
for hole in geometry['holes']:
    width, height = hole['drill']
    if abs(hole['rotation'] % 180 - 90) < 0.001:
        width, height = height, width
    target = (hole['plated'], hole['x'], hole['y'], width, height)
    index = next((i for i, row in enumerate(unmatched)
                  if row[0] == target[0] and max(abs(a-b) for a,b in zip(row[1:],target[1:])) <= 0.0011), None)
    assert index is not None, f'Missing or incorrect drill: {hole}'
    unmatched.pop(index)
assert not unmatched, f'Unexpected drills: {unmatched}'

extensions = {'.gtl', '.gbl', '.gts', '.gbs', '.gto', '.gbo', '.gm1', '.drl'}
files = sorted(p for p in folder.iterdir() if p.suffix.lower() in extensions)
assert len(files) == 9
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
report = {'created_utc': datetime.now(timezone.utc).isoformat(),
          'board_sha256': sha(root/'hardware/retro535.kicad_pcb'),
          'result': 'PASS', 'independent_parser': 'gerbonara',
          'layers': [list(x) for x in sorted(expected_layers)],
          'outline_closed': True, 'board_size_mm': size, 'drills': counts,
          'all_drills_match_board': True, 'coordinate_tolerance_mm': 0.0011,
          'parser_warnings': parser_warnings,
          'scope': 'Layer presence, outline endpoints and every drill; does not certify electrical function or JLCPCB DFM.',
          'files': {p.name: sha(p) for p in files}}
archive = root / 'fabrication/retro535-v1.0-jlcpcb.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for p in files:
        z.write(p, p.name)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert len(z.namelist()) == 9
    for p in files:
        assert hashlib.sha256(z.read(p.name)).hexdigest() == sha(p)
report['zip_sha256'] = sha(archive)
(root/'reports/manufacturing-audit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
(root/'fabrication/SHA256SUMS.txt').write_text(sha(archive)+'  '+archive.name+'\n', encoding='ascii')
print(json.dumps({k:v for k,v in report.items() if k not in ['files', 'layers']}, indent=2))
