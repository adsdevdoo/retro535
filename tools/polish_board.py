"""Final physical cleanup. Run after finish_board.py; always rerun KiCad DRC.
Uses retained SWIG wrapper lists: do not discard removed objects before saving.
"""
import pcbnew as p,pathlib,wx,math
wx.DisableAsserts()
root=pathlib.Path(__file__).resolve().parents[1];hw=root/'hardware';path=hw/'retro535.kicad_pcb';b=p.LoadBoard(str(path))
V=lambda x,y:p.VECTOR2I(p.FromMM(x+50),p.FromMM(y+50))
fps={f.GetReference():f for f in b.GetFootprints()};retained=[]
for t in b.GetTracks():
    if not isinstance(t,p.PCB_VIA) and t.GetWidth()<p.FromMM(.18):t.SetWidth(p.FromMM(.18))
for ref,pos in {'JP2':(12,59.8),'TP4':(16.6,57.5),'TP10':(52.5,11),'J7':(60,15),'R8':(12.5,30),'R23':(36.5,39.9),'D2':(63,5),'D3':(22,58.2),'U1':(21,22.2)}.items():fps[ref].Reference().SetPosition(V(*pos))
def board_text(txt,x,y,size=.9):
    t=p.PCB_TEXT(b);t.SetText(txt);t.SetPosition(V(x,y));t.SetLayer(p.F_SilkS);t.SetTextSize(p.VECTOR2I(p.FromMM(size),p.FromMM(size)));t.SetTextThickness(p.FromMM(.15));b.Add(t)
def shape(parent,typ,a,z,width=.15):
    s=p.PCB_SHAPE(parent);s.SetLayer(p.F_SilkS);s.SetShape(typ);s.SetStart(a);s.SetEnd(z);s.SetWidth(p.FromMM(width));parent.Add(s);return s
# Replace disconnected library orientation brackets with a complete rectangle.
for ref in ['U1','J2','J3','J4','J5','J6','J7','JP1','JP2','D2','D3']:
    fp=fps[ref];old=[g for g in fp.GraphicalItems() if isinstance(g,p.PCB_SHAPE) and g.GetLayer()==p.F_SilkS];retained+=old
    boxes=[g.GetBoundingBox() for g in old]
    x0=min(r.GetLeft() for r in boxes);x1=max(r.GetRight() for r in boxes);y0=min(r.GetTop() for r in boxes);y1=max(r.GetBottom() for r in boxes)
    for g in old:fp.Remove(g)
    if ref in ['D2','D3']:
        pos=fp.GetPosition();x0=pos.x-p.FromMM(2.2);x1=pos.x+p.FromMM(2.2);y0=pos.y-p.FromMM(1.15);y1=pos.y+p.FromMM(1.15)
    shape(fp,p.SHAPE_T_RECT,p.VECTOR2I(x0,y0),p.VECTOR2I(x1,y1))
# Keep the USB outline clear of the routed board edge.
for g in fps['J1'].GraphicalItems():
    if isinstance(g,p.PCB_SHAPE) and g.GetLayer()==p.F_SilkS:
        a,z=g.GetStart(),g.GetEnd();a.y=max(a.y,p.FromMM(50.3));z.y=max(z.y,p.FromMM(50.3));g.SetStart(a);g.SetEnd(z)
for t in b.GetDrawings():
    if isinstance(t,p.PCB_TEXT) and t.GetText()=='Pin1 / notch':t.SetText('1');t.SetPosition(V(31,20.6))
shape(b,p.SHAPE_T_SEGMENT,V(31,21.7),V(31,23.2))
shape(b,p.SHAPE_T_SEGMENT,V(31,23.2),V(30.5,22.7))
shape(b,p.SHAPE_T_SEGMENT,V(31,23.2),V(31.5,22.7))
board_text('K',57,7.2,.8);board_text('POWER',64,7,.8)
board_text('K',20,63.2,.8);board_text('P4.0',26.5,61,.8)
board_text('1',2,55,.8);board_text('1',10,62,.8);board_text('1',46,2.3,.8);board_text('1',56.6,12,.8)
# Direct connection on selected GND pads avoids isolated thermal spokes.
solid={'J1':{'A1','B12'},'J7':{'30'},'J2':{'10'},'J5':{'10'},'SW1':{'2'},'U1':{'51'},'U4':{'14'}}
for ref,pins in solid.items():
    for pad in fps[ref].Pads():
        if pad.GetNumber() in pins:pad.SetLocalZoneConnection(p.ZONE_CONNECTION_FULL)
filler=p.ZONE_FILLER(b);filler.Fill(b.Zones())
# Stitch only positions fully within GND copper on BOTH sides, clear of routing.
zones=list(b.Zones());centres=[(p.ToMM(t.GetPosition().x)-50,p.ToMM(t.GetPosition().y)-50) for t in b.GetTracks() if isinstance(t,p.PCB_VIA)]
candidates=[]
for yi in range(16):
    for xi in range(20):
        x,y=2.5+xi*5,2.5+yi*5
        if any((x-u)**2+(y-v)**2<4 for u,v in centres):continue
        good=all(z.HitTestFilledArea(z.GetLayer(),V(x+.46*math.cos(k*math.pi/6),y+.46*math.sin(k*math.pi/6))) for z in zones for k in range(12))
        if good:candidates.append((x,y));centres.append((x,y))
gnd=b.FindNet('GND')
for x,y in candidates:
    t=p.PCB_VIA(b);t.SetPosition(V(x,y));t.SetWidth(p.FromMM(.8));t.SetDrill(p.FromMM(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(gnd);b.Add(t)
filler.Fill(b.Zones());p.SaveBoard(str(path),b)
print('Closed outlines and explicit orientation marks; widened necks; added',len(candidates),'GND stitching vias')
