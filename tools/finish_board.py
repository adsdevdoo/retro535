"""Import routing into its matching placed board, add ground pours and presentation.
Usage with KiCad Python: finish_board.py --base ... --ses ...
"""
import pcbnew as p,wx,pathlib,argparse
wx.DisableAsserts()
ap=argparse.ArgumentParser();ap.add_argument('--base',required=True);ap.add_argument('--ses',required=True);a=ap.parse_args()
root=pathlib.Path(__file__).resolve().parents[1];hw=root/'hardware'
b=p.LoadBoard(a.base);assert p.ImportSpecctraSES(b,a.ses)
V=lambda x,y:p.VECTOR2I(p.FromMM(x+50),p.FromMM(y+50))
for item in b.GetDrawings():
    if isinstance(item,p.PCB_TEXT) and item.GetText()=='AN':item.SetPosition(V(5.5,68.2));item.SetText('ANALOG')
fps={f.GetReference():f for f in b.GetFootprints()}
for f in fps.values():
    f.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
    models=list(f.Models());f.Models().clear()
    for model in models:
        name=pathlib.Path(model.m_Filename).name
        if f.GetReference()=='U1':name='PLCC-68_THT-Socket.step'
        if (hw/'3d'/name).exists():model.m_Filename='${KIPRJMOD}/3d/'+name
        f.Add3DModel(model)
for ref,pos in {'J2':(20,75.5),'J3':(38,75.5),'J4':(55,75.5),'J6':(72,75.5),'J7':(57,14),'JP1':(44,5),'JP2':(12,60),
 'SW1':(13.2,48.5),'TP5':(48,63),'TP6':(52,63),'TP7':(48,67),'TP8':(52,67),'R15':(56,51.8),'U8':(53,38.5),'C20':(56.4,37),'U5':(10,13),'C15':(13.8,27),'C14':(32,35),'C10':(37,44.7)}.items():fps[ref].Reference().SetPosition(V(*pos))
gnd=b.FindNet('GND')
for layer in [p.F_Cu,p.B_Cu]:
    z=p.ZONE(b);z.SetLayer(layer);z.SetNet(gnd);z.SetLocalClearance(p.FromMM(.2));z.SetMinThickness(p.FromMM(.2));z.SetPadConnection(p.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(p.FromMM(.25));z.SetThermalReliefSpokeWidth(p.FromMM(.3));z.SetIslandRemovalMode(0)
    z.SetZoneName('GND_'+('top' if layer==p.F_Cu else 'bottom'))
    z.Outline().NewOutline()
    for x,y in [(0.5,0.5),(99.5,.5),(99.5,79.5),(.5,79.5)]:z.Outline().Append(V(x,y))
    b.Add(z)
filler=p.ZONE_FILLER(b);filler.Fill(b.Zones())
p.SaveBoard(str(hw/'retro535.kicad_pcb'),b)
print('Imported routing; filled both GND layers; saved',len(b.GetTracks()),'tracks/vias')
