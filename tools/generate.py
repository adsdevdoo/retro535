"""Generate native KiCad 9 schematics and project libraries from design.py.
No raster artwork is used as an electrical object. Each pin is a real symbol pin.
"""
from design import *
import uuid,shutil,csv
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'retro535/v1/'+s))
def q(s):return json.dumps(str(s),ensure_ascii=False)
def n(f):return f'{f:.4f}'.rstrip('0').rstrip('.')
def eff(size=1.0,justify=''):
    return f'(effects (font (size {size} {size})) {justify})'
HW=ROOT/'hardware';LIB=HW/'Retro535.pretty';LIB.mkdir(exist_ok=True)
KI=Path('C:/Program Files/KiCad/9.0/share/kicad/footprints')
# Exact pin-grid from KiCad, confirmed against Preci-Dip catalogue p94.
src=KI/'Package_LCC.pretty/PLCC-68_THT-Socket.kicad_mod'
s=src.read_text().replace('PLCC-68_THT-Socket','PLCC68_PreciDip_540-99-068-24-000-1')
s=s.replace('(descr "PLCC, 68 pins, through hole")','(descr "Preci-Dip 540-99-068-24-000-1; body 30.22 mm; outer drill grid 25.40 mm; inner 20.32 mm; catalogue p94")')
# Original courtyard/body is a generic ~31mm socket: retain the conservative courtyard.
socket_path=LIB/'PLCC68_PreciDip_540-99-068-24-000-1.kicad_mod'
if not socket_path.exists():socket_path.write_text(s)
for c in C:
    c['sch']=[round(v/1.27)*1.27 for v in c['sch']]
    if not c['fp'] or c['fp'].startswith('Retro535:'):continue
    lib,fp=c['fp'].split(':')
    source=KI/(lib+'.pretty')/(fp+'.kicad_mod')
    if not source.exists():raise FileNotFoundError(source)
    # Preserve reviewed silk geometry and local 3D paths. Refresh explicitly,
    # never overwrite edited library footprints when rebuilding the schematic.
    if not (LIB/(fp+'.kicad_mod')).exists():shutil.copy2(source,LIB/(fp+'.kicad_mod'))
    c['fp']='Retro535:'+fp

def symbol(c):
    name=c['ref'].replace('#','')+'_'+c['kind'];c['sym']=name
    pins=list(c['pins'])
    left=[str(x) for x in c['left']] if c['left'] else pins[:(len(pins)+1)//2]
    right=[x for x in pins if x not in left]
    if c['kind'] in ('header','tp','flag'):left=pins;right=[]
    c['locs']={};h=max(5.08,(max(len(left),len(right))+1)*2.54/2);w=17.78 if c['ref']=='U1' else 12.7
    if len(pins)<=2:w=3.81;h=2.54
    c['halfheight']=h;c['halfwidth']=w
    out=[f'(symbol {q(name)} (pin_names (offset 0.635)) (in_bom {"no" if c["kind"]=="flag" else "yes"}) (on_board {"no" if c["kind"]=="flag" else "yes"})',
         f'(property "Reference" {q(c["ref"])} (at 0 {n(h+2.54)} 0) {eff(1.27)})',
         f'(property "Value" {q(c["value"])} (at 0 {n(-h-2.54)} 0) {eff(1.0)})',
         f'(property "Footprint" {q(c["fp"])} (at 0 0 0) (effects (font (size 1 1)) (hide yes)))',
         f'(property "Datasheet" {q(c["source"])} (at 0 0 0) (effects (font (size 1 1)) (hide yes)))']
    shape=f'(rectangle (start {-w} {h}) (end {w} {-h}) (stroke (width 0.254) (type default)) (fill (type background)))'
    if c['kind']=='c':
        shape='(polyline (pts (xy -1 2.54) (xy -1 -2.54)) (stroke (width 0.254) (type default)) (fill (type none))) (polyline (pts (xy 1 2.54) (xy 1 -2.54)) (stroke (width 0.254) (type default)) (fill (type none)))'
        shape+=' (polyline (pts (xy -3.81 0) (xy -1 0)) (stroke (width 0) (type default)) (fill (type none))) (polyline (pts (xy 1 0) (xy 3.81 0)) (stroke (width 0) (type default)) (fill (type none)))'
    out.append(f'(symbol {q(name+"_0_1")} {shape})')
    out.append(f'(symbol {q(name+"_1_1")}')
    for side,seq in [('l',left),('r',right)]:
        for i,pin in enumerate(seq):
            y=(len(seq)-1)*1.27-i*2.54;x=(-1 if side=='l' else 1)*(w+2.54);angle=0 if side=='l' else 180
            pn,typ,net=c['pins'][pin];c['locs'][pin]=(x,y,side)
            pname='~' if len(pins)<=2 else pn
            out.append(f'(pin {typ} line (at {n(x)} {n(y)} {angle}) (length 2.54) (name {q(pname)} {eff(0.95)}) (number {q(pin)} {eff(0.9)}))')
    out+=[')',')']
    return '\n'.join(out)
symbols={c['ref']:symbol(c) for c in C}
(HW/'Retro535.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "retro535")\n'+'\n'.join(symbols.values())+'\n)',encoding='utf-8')
(HW/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "Retro535")(type "KiCad")(uri "${KIPRJMOD}/Retro535.kicad_sym")(options "")(descr "Retro535 local symbols")))')
(HW/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "Retro535")(type "KiCad")(uri "${KIPRJMOD}/Retro535.pretty")(options "")(descr "Vendored KiCad footprints and verified PLCC socket")))')
ROOTID=uid('root');SHEETIDS={i:uid('sheet'+str(i)) for i in range(2,5)}
titles={1:'USB-C, protection and enumerated power',2:'SAB80535-N core, reset, clock and analogue inputs',3:'External CODE and XDATA memory',4:'UART isolation, GPIO and test points'}
notes={
1:['JP1 OPEN for initial FT_PROG provisioning. Set bus power 500 mA, CBUS3=PWREN#, pull-down on suspend.',
   'Disconnect USB, fit JP1, reconnect. Main rail is off before enumeration and during USB suspend.',
   'No USB-PD. Use a data cable and a powered host/hub. Verify +5V > 4.75 V under load.',
   'F1 = resettable fuse; U6 = current/thermal limited switch. Shield bonded to GND.'],
2:['EA# = GND. RESET# is ACTIVE LOW (not standard 8051 polarity). VPD = GND.',
   'VBB pin 37: 100 nF to GND ONLY. Never tie VBB directly to either supply.',
   '11.0592 MHz; 30 pF C0G load capacitors. AN0..AN7: 100k weak pulldowns.',
   'P0 + P2 + P3.6/P3.7 + ALE/PSEN are reserved for memory. See connector sheet.'],
3:['CODE 0000..FFFF = Flash physical 00000..0FFFF. A16=0; upper 64 KiB unused.',
   'Flash /CE=0, /OE=/PSEN, /WE=+5V. REMOVE Flash with ALL POWER OFF for programming.',
   'XDATA 0000..7FFF = 32 KiB SRAM. /CE=A15, /OE=/RD, /WE=/WR. 8000..FFFF unpopulated.',
   'AS6C62256A (VIH=2.2V) is intentional; AS6C62256 without A has VIH=2.4V and zero high margin.'],
4:['J2/J3/J4: pins 1..8 = port bits 0..7; 9=+5V; 10=GND. 5V TTL, NOT 3.3V safe.',
   'J5: pins 1..8 = AN0..AN7; 9=AVREF output; 10=GND. Do not drive power/reference pins.',
   'J6: 1=RXD, 2=TXD, 3..6=P3.2..P3.5, 7=RESET#, 8=GND. Open JP2 for external RX source.',
   'U8 outputs disabled while RESET# is low. J7 is memory bus: probing only in v1.0.']}
def txt(text,x,y,size=1.3):return f'(text {q(text)} (at {x} {y} 0) {eff(size,"(justify left)")} (uuid {q(uid(text+str(x)+str(y)))}))'
for page in range(1,5):
    cs=[c for c in C if c['page']==page];sid=ROOTID if page==1 else uid('document'+str(page))
    path='/'+ROOTID+('' if page==1 else '/'+SHEETIDS[page])
    out=[f'(kicad_sch (version 20250114) (generator "eeschema") (uuid {q(sid)}) (paper "A3")',
         f'(title_block (title "Siemens SAB80535-N Retro Development Board") (date "2026-11-08") (rev "1.0") (company "retro535 - engineering prototype") (comment 1 {q(titles[page])}))',
         '(lib_symbols '+ '\n'.join(symbols[c['ref']].replace('(symbol '+q(c['sym']), '(symbol '+q('Retro535:'+c['sym']),1) for c in cs)+')',txt(titles[page],20,16,2.2)]
    for c in cs:
        x,y=c['sch'];symid=uid(c['ref']);c['uuid']=symid;c['path']=path
        out.append(f'(symbol (lib_id {q("Retro535:"+c["sym"])}) (at {x} {y} 0) (unit 1) (in_bom {"no" if c["kind"]=="flag" else "yes"}) (on_board {"no" if c["kind"]=="flag" else "yes"}) (dnp no) (uuid {q(symid)})')
        h=c['halfheight']
        for k,v,dy,hidden in [('Reference',c['ref'],-h-3.0,False),('Value',c['value'],-h-0.9,False),('Footprint',c['fp'],0,True),('Datasheet',c['source'],0,True),('MPN',c['mpn'],0,True)]:
            out.append(f'(property {q(k)} {q(v)} (at {x} {n(y+dy)} 0) (effects (font (size 1 1)) {"(hide yes)" if hidden else ""}))')
        for pin in c['pins']:out.append(f'(pin {q(pin)} (uuid {q(uid(c["ref"]+"pin"+pin))}))')
        out.append(f'(instances (project "retro535" (path {q(path)} (reference {q(c["ref"])}) (unit 1)))) )')
        for pin,(dx,dy,side) in c['locs'].items():
            px,py=x+dx,y-dy;pn,typ,net=c['pins'][pin]
            if net is None:
                out.append(f'(no_connect (at {n(px)} {n(py)}) (uuid {q(uid(c["ref"]+"nc"+pin))}))');continue
            lx=px+(-5.08 if side=='l' else 5.08);la=180 if side=='l' else 0
            out.append(f'(wire (pts (xy {n(px)} {n(py)}) (xy {n(lx)} {n(py)})) (stroke (width 0) (type default)) (uuid {q(uid(c["ref"]+"wire"+pin))}))')
            out.append(f'(global_label {q(net)} (shape bidirectional) (at {n(lx)} {n(py)} {la}) {eff(0.95,"(justify "+("right" if side=="l" else "left")+")")} (uuid {q(uid(c["ref"]+"label"+pin))}) (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {n(lx)} {n(py)} {la}) (effects (font (size 1 1)) (hide yes))))')
    for i,note in enumerate(notes[page]):out.append(txt(note,20,261+i*4,1.15))
    if page==1:
        # Child sheets use global nets; no hidden hierarchical wires.
        for i in range(2,5):
            sx=105+(i-2)*95;sy=219
            out.append(f'(sheet (at {sx} {sy}) (size 80 14) (stroke (width 0.254) (type default)) (fill (color 0 0 0 0)) (uuid {q(SHEETIDS[i])}) (property "Sheetname" {q(titles[i])} (at {sx} {sy-1} 0) {eff(1.0,"(justify left bottom)")}) (property "Sheetfile" {q("sheet"+str(i)+".kicad_sch")} (at {sx} {sy+15} 0) {eff(1.0,"(justify left top)")}) (instances (project "retro535" (path {q("/"+ROOTID)} (page {q(i)})))))')
        out.append('(sheet_instances (path "/" (page "1")))')
    out.append('(embedded_fonts no))')
    (HW/('retro535.kicad_sch' if page==1 else f'sheet{page}.kicad_sch')).write_text('\n'.join(out),encoding='utf-8')

# Rules are physical production targets, not disabled checks.
pro={'meta':{'filename':'retro535.kicad_pro','version':1},'board':{'design_settings':{'rules':{'min_clearance':0.18,'min_track_width':0.18,'min_via_diameter':0.6,'min_through_hole_diameter':0.3,'min_via_annular_width':0.15,'min_copper_edge_clearance':0.3,'min_hole_clearance':0.25,'min_silk_clearance':0.15,'min_silk_text_height':0.8,'min_silk_text_thickness':0.12},'defaults':{'board_outline_line_width':0.05},'rule_severities':{'silk_over_copper':'warning','silk_overlap':'warning'}}},'net_settings':{'classes':[{'name':'Default','clearance':0.20,'track_width':0.25,'via_diameter':0.65,'via_drill':0.3,'microvia_diameter':0.3,'microvia_drill':0.1,'diff_pair_width':0.25,'diff_pair_gap':0.2,'diff_pair_via_gap':0.25},{'name':'Power','clearance':0.20,'track_width':0.6,'via_diameter':0.8,'via_drill':0.4,'microvia_diameter':0.3,'microvia_drill':0.1,'diff_pair_width':0.25,'diff_pair_gap':0.2,'diff_pair_via_gap':0.25}], 'netclass_patterns':[{'netclass':'Power','pattern':v} for v in ['VBUS','VBUS_F','+5V_USB','+5V']]}}
rules=pro['board']['design_settings']['rules']
rules['min_text_height']=rules.pop('min_silk_text_height');rules['min_text_thickness']=rules.pop('min_silk_text_thickness');rules['min_via_annular_width']=.18
rules.update(min_text_height=1.0,min_text_thickness=.15)  # JLCPCB silk capability
pro['net_settings']['classes'][0]['via_diameter']=.7
pro['net_settings']['classes'][1].update(track_width=.4,via_diameter=.8,via_drill=.3)
(HW/'retro535.kicad_pro').write_text(json.dumps(pro,indent=2))
(HW/'design.json').write_text(json.dumps(C,indent=2),encoding='utf-8')
with (ROOT/'docs/BOM.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['Reference','Qty','Value','MPN','Footprint','Datasheet','Notes'])
    for c in C:
        if c['kind']=='flag':continue
        w.writerow([c['ref'],1,c['value'],c['mpn'],c['fp'],c['source'],'EOL; no substitution without level review' if c['ref']=='U4' else 'Supplied by user; socket listed separately' if c['ref']=='U1' else 'Fit only after USB provisioning' if c['ref']=='JP1' else ''])
    w.writerow(['U1 socket',1,'PLCC-68 THT','540-99-068-24-000-1','Retro535:PLCC68_PreciDip_540-99-068-24-000-1','https://static.chipdip.ru/lib/825/DOC031825282.pdf','Preci-Dip, catalogue p94'])
    w.writerow(['U3 socket',1,'DIP32 600mil','110-93-632-41-001000','included with U3','','Mill-Max; 2.54mm pitch'])
    w.writerow(['U4 socket',1,'DIP28 600mil','110-93-628-41-001000','included with U4','','Mill-Max; 2.54mm pitch'])
    w.writerow(['JP1/JP2 shunts',2,'2.54mm shunt','QPC02SXGN-RC','n/a','','Sullins; fit JP1 only after FT_PROG provisioning'])
print('Generated',len(C),'symbols, four schematic pages and local libraries')
