"""Apply small DRC-driven geometry corrections after polish_board.py.
Run with KiCad Python. Re-running is harmless (exact old coordinates only).
"""
import pathlib
import pcbnew as p
root=pathlib.Path(__file__).resolve().parents[1]
path=root/'hardware/retro535.kicad_pcb'
b=p.LoadBoard(str(path))
moves={
 'D5':{(90.1762,81.7058):(90.1462,81.7058),(90.1762,82.6937):(90.1462,82.6937)},
 'CC2':{(62.1752,59.6628):(62.1452,59.6628),(62.1752,59.5881):(62.1452,59.5881),(62.0312,59.8068):(62.0012,59.8068)},
 'UART_RX_BUF':{(94.7374,111.0186):(94.7574,111.0186),(94.7374,110.7009):(94.7574,110.7009)}
}
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA) or t.GetNetname() not in moves:continue
 for getter,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
  v=getter();key=(round(p.ToMM(v.x),4),round(p.ToMM(v.y),4))
  if key in moves[t.GetNetname()]:
   x,y=moves[t.GetNetname()][key];setter(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
for t in b.GetDrawings():
 if isinstance(t,p.PCB_TEXT) and t.GetText()=='USB-C 5V':
  t.SetPosition(p.VECTOR2I(p.FromMM(63),p.FromMM(51.15)))
for f in b.GetFootprints():
 if f.GetReference().startswith('H'):
  f.SetAttributes(f.GetAttributes() | p.FP_BOARD_ONLY)
filler=p.ZONE_FILLER(b);filler.Fill(b.Zones())
p.SaveBoard(str(path),b)
print('Adjusted clearance bottlenecks; refilled zones.')
