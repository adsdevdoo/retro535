"""Reconcile explicit NC nets/BOM flags and save reviewed footprints locally.
Run with KiCad Python, after exporting reports/netlist.xml. Does not reroute.
"""
from pathlib import Path
import xml.etree.ElementTree as E
import pcbnew as p
root=Path(__file__).resolve().parents[1];hw=root/'hardware'
b=p.LoadBoard(str(hw/'retro535.kicad_pcb'))
fps={f.GetReference():f for f in b.GetFootprints()}
tree=E.parse(root/'reports/netlist.xml')
changed=[]
for net in tree.findall('./nets/net'):
    name=net.attrib['name']
    for node in net.findall('node'):
        ref,pin=node.attrib['ref'],node.attrib['pin']
        if ref not in fps:continue
        for pad in fps[ref].Pads():
            if pad.GetNumber()!=pin:continue
            if pad.GetNetname()==name:continue
            assert name.startswith('unconnected-') and not pad.GetNetname(),(ref,pin,pad.GetNetname(),name)
            target=b.FindNet(name)
            if not target:target=p.NETINFO_ITEM(b,name);b.Add(target)
            pad.SetNet(target);changed.append(ref+'.'+pin)
for ref,f in fps.items():
    if ref.startswith('TP'):
        f.SetAttributes(f.GetAttributes() & ~p.FP_EXCLUDE_FROM_BOM)

# Models and closed silk outlines are part of the local library as well as PCB.
plugin=p.PCB_IO_MGR.PluginFind(p.PCB_IO_MGR.KICAD_SEXP)
saved=set();clones=[]
for f in sorted(fps.values(),key=lambda f:f.GetReference()):
    name=str(f.GetFPID().GetLibItemName())
    if name in saved:continue
    g=f.Duplicate();clones.append(g)
    if g.IsFlipped():g.Flip(g.GetPosition(),False)
    g.SetOrientationDegrees(0);g.SetPosition(p.VECTOR2I(0,0))
    g.SetReference('REF**');g.SetValue(name)
    plugin.FootprintSave(str((hw/'Retro535.pretty').resolve()).replace('\\','/'),g)
    saved.add(name)
p.SaveBoard(str(hw/'retro535.kicad_pcb'),b)
print('NC nets assigned:',len(changed),'Library footprints:',len(saved))
