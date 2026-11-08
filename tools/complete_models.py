"""Attach the reviewed local display models; run with KiCad Python.

No pad, track, hole or component position is modified. Models are visual aids;
see docs/models.md for provenance and approximation limits.
"""
from pathlib import Path
import shutil
import pcbnew as p

root=Path(__file__).resolve().parents[1]
hw=root/'hardware'
models=hw/'3d'
kicad_models=Path('C:/Program Files/KiCad/9.0/share/kicad/3dmodels')
shutil.copy2(models/'sources/MF-MSMF075_adom.step',models/'MF-MSMF075_adom_illustrative.step')
shutil.copy2(kicad_models/'Crystal.3dshapes/Crystal_HC49-4H_Vertical.step',models/'Crystal_HC49-4H_Vertical.step')
b=p.LoadBoard(str(hw/'retro535.kicad_pcb'))
for f in b.GetFootprints():
    if f.GetReference()=='F1':
        f.Models().clear()
        m=p.FP_3DMODEL()
        m.m_Filename='${KIPRJMOD}/3d/MF-MSMF075_adom_illustrative.step'
        # Downloaded nominal height is 0.9 mm. Bourns MF-MSMF075 body C is
        # 0.55..0.85 mm: use 0.70 mm, retaining X=4.52 and Y=3.22 mm.
        m.m_Scale.z=0.7/0.9
        f.Add3DModel(m)
    elif f.GetReference()=='Y1':
        f.Models().clear()
        m=p.FP_3DMODEL()
        m.m_Filename='${KIPRJMOD}/3d/Crystal_HC49-4H_Vertical.step'
        # Generic HC49 low-profile shell; ECS -4X height envelope is 3.5 mm.
        # XY hole pitch remains 4.88 mm. Not manufacturer's detailed CAD.
        m.m_Scale.z=3.5/4.1
        f.Add3DModel(m)
        # The authoritative MPN and datasheet are regenerated in the schematic
        # and BOM by generate.py; FOOTPRINT has no SetProperty in KiCad 9.
p.SaveBoard(str(hw/'retro535.kicad_pcb'),b)
print('F1 and Y1 models attached; electrical geometry unchanged.')
