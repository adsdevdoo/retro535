"""Check every PCB footprint's local model files. Run with KiCad Python.
File checks do not certify mechanical fit; read docs/models.md and inspect renders.
"""
from pathlib import Path
import hashlib,json,re
from datetime import datetime,timezone
import pcbnew as p
root=Path(__file__).resolve().parents[1];hw=root/'hardware'
board=hw/'retro535.kicad_pcb';b=p.LoadBoard(str(board))
items=[]
def natural(s):return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)',s)]
for f in sorted(b.GetFootprints(),key=lambda f:natural(f.GetReference())):
    ref=f.GetReference();exception='bare PCB test pad' if ref.startswith('TP') else 'mounting hole; hardware not fitted' if ref.startswith('H') else None
    row={'reference':ref,'value':f.GetValue(),'footprint':str(f.GetFPID().GetLibItemName()),'side':'bottom' if f.IsFlipped() else 'top','exception':exception,'models':[]}
    for m in f.Models():
        path=Path(m.m_Filename.replace('${KIPRJMOD}',str(hw)))
        row['models'].append({'path':m.m_Filename,'exists':path.is_file(),'project_local':m.m_Filename.startswith('${KIPRJMOD}/3d/'),'sha256':hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None,'scale':[m.m_Scale.x,m.m_Scale.y,m.m_Scale.z],'offset_mm':[m.m_Offset.x,m.m_Offset.y,m.m_Offset.z],'rotation_deg':[m.m_Rotation.x,m.m_Rotation.y,m.m_Rotation.z]})
    row['file_check_pass']=bool(exception) or (bool(row['models']) and all(m['exists'] and m['project_local'] for m in row['models']))
    row['display_state']='empty socket; removable IC deliberately omitted' if ref in ['U1','U3','U4'] else 'no discrete component' if exception else 'component body'
    row['mechanical_validation']='not manufacturer CAD certification; see docs/models.md'
    items.append(row)
result={'created_utc':datetime.now(timezone.utc).isoformat(),'board_sha256':hashlib.sha256(board.read_bytes()).hexdigest(),'scope':'model-file coverage, portable paths, transforms and hashes; not mechanical collision certification','footprints':len(items),'requires_model':sum(not bool(i['exception']) for i in items),'missing_or_nonportable':[i['reference'] for i in items if not i['file_check_pass']],'items':items}
(root/'reports/models-audit.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='items'},ensure_ascii=False))
raise SystemExit(bool(result['missing_or_nonportable']))
