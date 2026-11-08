import pcbnew as p,pathlib,json,math
root=pathlib.Path(__file__).resolve().parents[1];b=p.LoadBoard(str(root/'hardware/retro535.kicad_pcb'))
holes=[]
for f in b.GetFootprints():
 for pad in f.Pads():
  d=pad.GetDrillSize();v=pad.GetPosition()
  if not d.x:continue
  holes.append({'ref':f.GetReference(),'pin':pad.GetNumber(),'x':p.ToMM(v.x),'y':-p.ToMM(v.y),'drill':[p.ToMM(d.x),p.ToMM(d.y)],'rotation':pad.GetOrientationDegrees(),'plated':pad.GetAttribute()!=p.PAD_ATTRIB_NPTH})
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA):
  v=t.GetPosition();d=p.ToMM(t.GetDrillValue());holes.append({'ref':'via','pin':'','x':p.ToMM(v.x),'y':-p.ToMM(v.y),'drill':[d,d],'rotation':0,'plated':True})
edges=[g for g in b.GetDrawings() if isinstance(g,p.PCB_SHAPE) and g.GetLayer()==p.Edge_Cuts]
pts=[(round(p.ToMM(v.x),5),round(-p.ToMM(v.y),5)) for g in edges for v in [g.GetStart(),g.GetEnd()]]
from collections import Counter
assert len(edges)==10 and all(x==2 for x in Counter(pts).values())
xs,ys=zip(*pts);size=[max(xs)-min(xs),max(ys)-min(ys)];assert size==[100,80]
tracks=[t for t in b.GetTracks() if not isinstance(t,p.PCB_VIA)]
data={'board_size_mm':size,'outline_closed':True,'copper_layers':b.GetCopperLayerCount(),'min_track_mm':min(p.ToMM(t.GetWidth()) for t in tracks),'tracks':len(tracks),'holes':holes,'outline_vertices':sorted(set(pts))}
(root/'reports/pcb-geometry.json').write_text(json.dumps(data,indent=2));print({k:v for k,v in data.items() if k!='holes'})
