"""Build with SDCC 4.5+ and generate complete erased-filled programmer images."""
import argparse, hashlib, pathlib, shutil, subprocess, os
p=argparse.ArgumentParser();p.add_argument('--sdcc',default=shutil.which('sdcc'));a=p.parse_args()
if not a.sdcc: p.error('install SDCC or pass --sdcc /path/to/sdcc')
root=pathlib.Path(__file__).resolve().parent;out=root/'build';out.mkdir(exist_ok=True)
cmd=[a.sdcc,'-mmcs51','--model-small','--iram-size','256','--code-size','65536','--xram-size','32768','--out-fmt-ihx','--debug',str(root/'main.c'),'-o','retro535.ihx']
env=dict(os.environ);env['PATH']=str(pathlib.Path(a.sdcc).resolve().parent)+os.pathsep+env.get('PATH','')
subprocess.run(cmd,cwd=out,env=env,check=True)
rom=bytearray([255])*131072;base=0;used=0
for line in (out/'retro535.ihx').read_text().splitlines():
    if not line.startswith(':'): continue
    r=bytes.fromhex(line[1:]);assert sum(r)&255==0,'Intel HEX checksum'
    n,hi,lo,kind=r[:4];addr=base+(hi<<8)+lo
    if kind==0:
        assert addr+n<=65536,'CODE exceeds the connected lower bank'
        rom[addr:addr+n]=r[4:4+n];used=max(used,addr+n)
    elif kind==4: base=int.from_bytes(r[4:6],'big')<<16
    elif kind==1: break
for name,data in [('retro535-code64k.bin',rom[:65536]),('retro535-sst39sf010a-128k.bin',rom)]:
    (out/name).write_bytes(data)
(out/'SHA256SUMS').write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.name+'\n' for f in sorted(out.glob('*.bin'))))
print(f'CODE extent: {used} bytes. Programmer image: 131072 bytes; A16=0 on board.')
