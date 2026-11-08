"""Reviewed manual power routing and GND stitching after Specctra import.
Run once after finish_board.py, with KiCad Python. All results require DRC.
"""
import pcbnew as p,pathlib,math,wx
wx.DisableAsserts()
root=pathlib.Path(__file__).resolve().parents[1];path=root/'hardware/retro535.kicad_pcb';b=p.LoadBoard(str(path))
V=lambda x,y:p.VECTOR2I(p.FromMM(x+50),p.FromMM(y+50))
def track(net,pts,layer=p.F_Cu,width=.4):
    for a,z in zip(pts,pts[1:]):
        t=p.PCB_TRACK(b);t.SetStart(V(*a));t.SetEnd(V(*z));t.SetWidth(p.FromMM(width));t.SetLayer(layer);t.SetNet(b.FindNet(net));b.Add(t)
def via(net,x,y,d=.8,h=.3):
    t=p.PCB_VIA(b);t.SetPosition(V(x,y));t.SetWidth(p.FromMM(d));t.SetDrill(p.FromMM(h));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(b.FindNet(net));b.Add(t)
# Replace the autorouter's crossing beside TP2 with a bottom-layer power bridge.
bad={'3a2721d3-33c2-4233-98a3-58b55fecb4b4','3d857d5b-05a9-428b-a37a-80e3c7e66ac3','4ecf09fe-5bc1-4336-9717-2bd21f7192c7','8ea24592-4ee9-4376-bb9e-1779babd0dfe','971ed206-2891-4225-8dd9-1a1d25160ce5','b0b4c5cf-8230-4717-86be-b3566b557feb','bfcfaac8-bd7f-4949-bb77-4a5031ccee9d','f625ba56-4bf0-416a-8626-b9a8be4293b9'}
removed=0
original_tracks=list(b.GetTracks()) # keep SWIG wrappers alive until the board is saved
for t in original_tracks:
    if t.m_Uuid.AsString() in bad:b.Remove(t);removed+=1
assert removed==len(bad),'Run against the matching reviewed import, not a different route'
print('removed crossing',len(b.Zones()),flush=True)
track('+5V',[(83.6222,3.4983),(84.8,3.4983),(84.8,3.4)],width=.6)
via('+5V',84.8,3.4,.9,.4)
track('+5V',[(84.8,3.4),(84.8,7.1),(85.2,7.5)],p.B_Cu,.6)
via('+5V',85.2,7.5,.9,.4)
track('+5V',[(85.2,7.5),(85.8083,8.1083),(95.1218,8.1083)],width=.6)
print('main bridge added',len(b.Zones()),flush=True)
# USB VBUS breakout: short neckdowns at the connector, then wider trunk.
track('VBUS',[(16.45,8.045),(16.45,7.2),(15.8,6.55),(15.8,5.8)],width=.3)
track('VBUS',[(11.55,8.045),(11.55,7.3),(12,6.85),(12,5.8)],width=.3)
via('VBUS',15.8,5.8);via('VBUS',12,5.8)
track('VBUS',[(12,5.8),(12,4.9),(15.8,4.9),(15.8,5.8)],p.B_Cu,.6)
track('VBUS',[(15.8,4.9),(21,4.9),(21,5)],p.B_Cu,.6);via('VBUS',21,5)
track('VBUS',[(21,5),(22.8625,5),(22.8625,2.7),(24.0625,1.5),(26.9625,1.5)],width=.6)
track('VBUS',[(15.1375,11.4),(17.2,11.4)],width=.3);via('VBUS',17.2,11.4)
track('VBUS',[(17.2,11.4),(17.2,8.7),(15.8,7.3),(15.8,5.8)],p.B_Cu,.4)
print('VBUS added',len(b.Zones()),flush=True)
# Refill before selecting stitching positions from real ground polygons.
zones=list(b.Zones());filler=p.ZONE_FILLER(b);filler.Fill(b.Zones())
centres=[(p.ToMM(x.GetPosition().x)-50,p.ToMM(x.GetPosition().y)-50) for x in b.GetTracks() if isinstance(x,p.PCB_VIA)]
for f in b.GetFootprints():
    for pad in f.Pads():
        if pad.GetNetname()=='GND' and pad.GetAttribute()==p.PAD_ATTRIB_PTH:centres.append((p.ToMM(pad.GetPosition().x)-50,p.ToMM(pad.GetPosition().y)-50))
def clear_ground(x,y):
    if any((x-u)**2+(y-v)**2<2.0**2 for u,v in centres):return False
    for z in zones:
        for k in range(12):
            th=k*math.pi/6
            if not z.HitTestFilledArea(z.GetLayer(),V(x+.46*math.cos(th),y+.46*math.sin(th))):return False
    return True
count=0
for yi in range(16):
    for xi in range(20):
        x,y=2.5+xi*5,2.5+yi*5
        if clear_ground(x,y):via('GND',x,y);centres.append((x,y));count+=1
filler.Fill(b.Zones())
p.SaveBoard(str(path),b)
print('Manual power fixes applied; added',count,'ground stitching vias')
