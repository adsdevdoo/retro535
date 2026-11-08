"""Run with KiCad 9 bin/python.exe. Create placed, electrically linked PCB.
Export DSN for external routing; final checks run in KiCad CLI, not in router.
"""
import pcbnew as p, json, pathlib, wx
wx.DisableAsserts()
ROOT=pathlib.Path(__file__).resolve().parents[1];HW=ROOT/'hardware'
cs=json.loads((HW/'design.json').read_text(encoding='utf8'))
b=p.BOARD();b.SetCopperLayerCount(2);b.SetFileName(str(HW/'retro535.kicad_pcb'))
V=lambda x,y:p.VECTOR2I(p.FromMM(x+50),p.FromMM(y+50))
nets={}
for net in sorted({pin[2] for c in cs for pin in c['pins'].values() if pin[2]}):
    nn=p.NETINFO_ITEM(b,net);b.Add(nn);nets[net]=nn
ds=b.GetDesignSettings();ds.m_MinClearance=p.FromMM(.18);ds.m_TrackMinWidth=p.FromMM(.18);ds.m_ViasMinSize=p.FromMM(.6);ds.m_MinThroughDrill=p.FromMM(.3)
ds.m_CopperEdgeClearance=p.FromMM(.3)
ds.m_NetSettings.GetDefaultNetclass().SetTrackWidth(p.FromMM(.25))
ds.m_NetSettings.GetDefaultNetclass().SetClearance(p.FromMM(.2))
ds.m_NetSettings.GetDefaultNetclass().SetViaDiameter(p.FromMM(.7))
ds.m_NetSettings.GetDefaultNetclass().SetViaDrill(p.FromMM(.3))
power=p.NETCLASS('Power');power.SetClearance(p.FromMM(.2));power.SetTrackWidth(p.FromMM(.4));power.SetViaDiameter(p.FromMM(.8));power.SetViaDrill(p.FromMM(.3))
ds.m_NetSettings.SetNetclass('Power',power)
for name in ['VBUS','VBUS_F','+5V_USB','+5V']:
    ds.m_NetSettings.SetNetclassPatternAssignment(name,'Power');nets[name].SetNetClass(power)
fps={}
back={'C10','C11','C12','C13','C14'}|{f'R{i}' for i in range(20,28)}
overrides={'J1':(14,4),'D1':(14,11.4),'U1':(31,27),'U2':(53,29),'U5':(10,19.3),'U8':(53,44),
 'U7':(7,35),'TP4':(13,57.5),'TP9':(11,54),'C15':(10,27),'C16':(5,27),'R8':(9,30),'TP10':(52.5,9),
 'U3':(61,23),'U4':(80.5,23),'C18':(76,20),'C19':(95,20),'TP1':(88,5),'TP2':(83,5),'TP3':(78,5),
 'R1':(6,10.5),'R2':(22,10.5),'C3':(18,20),'C4':(3,20),'C5':(18,15),
 'R3':(23,14),'R5':(42,18),'C8':(44,20),'Q1':(51,20),'R11':(47,16),'R12':(53,16),'R13':(47,12),
 'C20':(53,37),'JP2':(12,62),'C9':(5,41),'R7':(11.5,40),'C2':(28,1.5),'C17':(57,19),'C10':(37,46.5),'C11':(36,55.3),'C12':(30.5,55),'C13':(34,32.5),'C14':(36,35),'Y1':(37,60),
 'TP5':(48,61),'TP6':(52,61),'TP7':(48,65),'TP8':(52,65)}
for i in range(8):overrides[f'R{20+i}']=(24.5+(i%4)*4,38+(i//4)*5)
for c in cs:
    if not c['fp']:continue
    fpname=c['fp'].split(':')[1];fp=p.FootprintLoad(str(HW/'Retro535.pretty'),fpname)
    if fp is None:raise RuntimeError(fpname)
    fp.SetReference(c['ref']);fp.SetValue(c['value']);fp.SetFPID(p.LIB_ID('Retro535',fpname))
    kp=p.KIID_PATH()
    for item in (c['path']+'/'+c['uuid']).strip('/').split('/'):kp.push_back(p.KIID(item))
    fp.SetPath(kp)
    b.Add(fp)
    pos=overrides.get(c['ref'],c['xy']);fp.SetPosition(V(*pos));fp.SetOrientationDegrees(180 if c['ref']=='J1' else c['angle'])
    if c['ref'] in back:fp.Flip(fp.GetPosition(),False)
    fp.Reference().SetTextSize(p.VECTOR2I(p.FromMM(.85),p.FromMM(.85)));fp.Reference().SetTextThickness(p.FromMM(.13))
    fp.Value().SetVisible(False)
    for pad in fp.Pads():
        num=pad.GetNumber()
        if not num:continue
        if num not in c['pins']:raise RuntimeError(f'{c["ref"]} missing pin {num}')
        net=c['pins'][num][2]
        if net:pad.SetNet(nets[net])
        if c['ref']=='J1':pad.SetLocalClearance(p.FromMM(.2))
    fps[c['ref']]=fp

for i,(x,y) in enumerate([(4,4),(96,4),(4,76),(96,76)],1):
    fp=p.FootprintLoad('C:/Program Files/KiCad/9.0/share/kicad/footprints/MountingHole.pretty','MountingHole_3.2mm_M3');fp.SetReference('H'+str(i));fp.SetValue('M3 NPTH');fp.SetPosition(V(x,y));fp.Value().SetVisible(False);fp.Reference().SetVisible(False);b.Add(fp)
    fp.SetAttributes(fp.GetAttributes()|p.FP_EXCLUDE_FROM_BOM|p.FP_EXCLUDE_FROM_POS_FILES)
for a,z in [((0,0),(100,0)),((100,0),(100,80)),((100,80),(0,80)),((0,80),(0,0))]:
    s=p.PCB_SHAPE();s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(V(*a));s.SetEnd(V(*z));s.SetLayer(p.Edge_Cuts);s.SetWidth(p.FromMM(.05));b.Add(s)
def text(txt,x,y,size=1,layer=p.F_SilkS,angle=0):
    t=p.PCB_TEXT(b);t.SetText(txt);t.SetPosition(V(x,y));t.SetTextSize(p.VECTOR2I(p.FromMM(size),p.FromMM(size)));t.SetTextThickness(p.FromMM(.15));t.SetLayer(layer);t.SetTextAngle(p.EDA_ANGLE(angle,p.DEGREES_T));
    if layer==p.B_SilkS:t.SetMirrored(True)
    b.Add(t)
text('retro535  v1.0',58,2,1.15)
text('Siemens SAB80535-N',32,64,1.05)
text('PLCC-68 socket',30,67,0.9)
text('FLASH / REMOVE TO PROGRAM',70,65,0.8)
text('SRAM 32K',91,60,0.85)
text('USB-C 5V',13,1,0.8)
text('RUN',49,8,0.8)
text('RESET',7,51,0.9)
text('P1',20,68,0.9);text('P4',38,68,0.9);text('P5',55,68,0.9);text('UART/P3',72,68,0.8)
text('AN',4,51,0.9);text('BUS: NOT GPIO',76,7,0.8)
text('1',12.3,73,0.85);text('1',30.3,73,0.85);text('1',47.3,73,0.85);text('1',65.3,73,0.85)
text('Pin1 / notch',29,22,0.8)
text('retro535 v1.0',84,63,1.1,p.B_SilkS)
text('100 x 80 mm',84,65,.9,p.B_SilkS)
text('J2=P1  J3=P4  J4=P5: 1..8 = bit0..7 / 9=5V / 10=GND',52,68,.8,p.B_SilkS)
text('JP1: fit after FT_PROG 500mA / PWREN / suspend pull-down',50,77,.8,p.B_SilkS)
text('Engineering prototype - not hardware validated',52,16,.9,p.B_SilkS)
# Short sensitive connections are routed before the general bus routing.
def track(net,points,layer=p.F_Cu,width=.25):
    for a,z in zip(points,points[1:]):
        t=p.PCB_TRACK(b);t.SetStart(V(*a));t.SetEnd(V(*z));t.SetWidth(p.FromMM(width));t.SetLayer(layer);t.SetNet(nets[net]);t.SetLocked(True);b.Add(t)
def via(net,x,y):
    t=p.PCB_VIA(b);t.SetPosition(V(x,y));t.SetWidth(p.FromMM(.8));t.SetDrill(p.FromMM(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(nets[net]);t.SetLocked(True);b.Add(t)
track('XTAL1',[(36.08,49.86),(37.0375,48.9025),(37.0375,47.5),(38.0375,46.5),(39.3,47.7625),(39.3,48),(39.89,48.59),(39.89,53.8),(41.88,55.79),(41.88,60)],p.B_Cu)
track('XTAL2',[(36.08,52.4),(37.0375,53.3575),(37.0375,55.3),(37.0375,59.9625),(37,60)],p.B_Cu)
track('VBB',[(33.54,52.4),(33.54,52.9975),(31.5375,55)],p.B_Cu)
track('+5V',[(33.54,29.54),(35.0375,31.0375),(35.0375,32.5),(35.0375,33),(37.0375,35)],p.B_Cu,.4)
track('USB_DP',[(14.25,8.045),(14.25,9.15),(13.25,9.15),(13.25,8.045)])
track('USB_DP',[(13.25,9.15),(12.5,9.9),(12.5,10.45),(12.8625,10.45),(15.1375,10.45)])
track('USB_DP',[(12.8625,10.45),(11.5,10.45),(7.5,14.45),(6.4,14.45),(6.4,15.075)])
track('USB_DM',[(13.75,8.045),(13.75,6.5)])
via('USB_DM',13.75,6.5)
track('USB_DM',[(14.75,8.045),(14.75,8.9),(15.55,9.7),(16.5,9.7)])
via('USB_DM',16.5,9.7)
track('USB_DM',[(13.75,6.5),(16.5,9.65),(16.5,13.5)],p.B_Cu)
via('USB_DM',16.5,13.5)
track('USB_DM',[(16.5,13.5),(15.35,12.35),(15.1375,12.35),(12.8625,12.35),(11.5,12.35),(8.125,15.725),(6.4,15.725)])
# VBUS precedes signal routing so that CC and shield connections route around it.
track('VBUS',[(16.45,8.045),(16.45,7.2),(15.8,6.55),(15.8,5.8)],width=.3)
track('VBUS',[(11.55,8.045),(11.55,7.3),(12,6.85),(12,5.8)],width=.3)
via('VBUS',15.8,5.8);via('VBUS',12,5.8)
track('VBUS',[(12,5.8),(12,4.9),(15.8,4.9),(15.8,5.8)],p.B_Cu,.6)
track('VBUS',[(15.8,4.9),(21,4.9),(21,5)],p.B_Cu,.6);via('VBUS',21,5)
track('VBUS',[(21,5),(22.8625,5),(22.8625,2.7),(24.0625,1.5),(26.9625,1.5)],width=.6)
track('VBUS',[(15.1375,11.4),(17.4,11.4)],width=.3);via('VBUS',17.4,11.4)
track('VBUS',[(17.4,11.4),(17.4,8.9),(15.8,7.3),(15.8,5.8)],p.B_Cu,.4)
# Reference relocation does not change connectivity.
for ref,pos in {'C2':(32,1.5),'SW1':(3,42),'J1':(14,5),'D1':(17.5,11.4),'TP5':(47,62.5),'R15':(58.8,50),'C8':(44,21.8),'C12':(30,56.9),'C11':(36,57),'C10':(41,57),'C14':(36,36.8),'C15':(10,29),'C20':(53,38.8),'U5':(10,13.6)}.items():
    fps[ref].Reference().SetPosition(V(*pos));fps[ref].Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
# Ground zones are added after routing, followed by a full KiCad DRC.
p.SaveBoard(str(HW/'retro535.kicad_pcb'),b)
p.ExportSpecctraDSN(b,str(ROOT/'reports/retro535.dsn'))
print('PCB saved:',len(fps),'footprints;',len(nets),'nets; 100 x 80 mm; 2 copper layers')

