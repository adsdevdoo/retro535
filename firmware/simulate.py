"""Instruction-level smoke test, not a SAB80535-N electrical model.
Runs the SAME HEX used for programming. Requires uCsim s51 (SDCC bundle).
"""
import argparse,pathlib,re,shutil,subprocess,json
p=argparse.ArgumentParser();p.add_argument('--s51',default=shutil.which('s51'));a=p.parse_args()
if not a.s51:p.error('install uCsim or pass --s51 /path/to/s51')
root=pathlib.Path(__file__).resolve().parent;out=root/'build';reports=root.parent/'reports'
mapping=(out/'retro535.map').read_text()
def sym(n):return int(re.search(r'^\s*(?:C:\s*)?([0-9A-Fa-f]{8})\s+_'+n+r'\s',mapping,re.M)[1],16)
done=sym('tests_complete');verify=sym('address_verify_start');status=sym('test_status')
results={}
for case in ['normal','injected_fault']:
    uart=reports/('sim-'+case+'-uart.txt')
    if uart.exists():uart.unlink()
    commands=[]
    if case=='injected_fault':
        commands += [f'tbreak 0x{verify:x}','step 8000000','set memory xram 0 0x55']
    commands += [f'tbreak 0x{done:x}','step 12000000',f'dump iram 0x{status:x} 0x{status+4:x}',
                 'tbreak sfr w 0xe8','step 2000000','dump sfr 0xe8 0xe8',
                 'tbreak sfr w 0xe8','step 2000000','dump sfr 0xe8 0xe8','quit']
    cfg='\n'.join(commands)+'\n'
    (reports/('sim-'+case+'.cmd')).write_text(cfg)
    result=subprocess.run([a.s51,'-t','C52','-X','11059200','-q','-b','-c','-',
                          '-S','uart=0,out='+str(uart),'retro535.ihx'],cwd=out,
                          input=cfg,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=90)
    (reports/('sim-'+case+'-console.txt')).write_text(result.stdout)
    tx=uart.read_text(errors='replace') if uart.exists() else ''
    expected='SRAM PASS 32768 bytes' if case=='normal' else 'SRAM FAIL @0000 expected=00 actual=55'
    assert expected in tx,(case,tx,result.stdout[-2500:])
    assert re.search(r'0xe8\s+fe',result.stdout,re.I), 'LED active-low transition not observed'
    assert re.search(r'0xe8\s+ff',result.stdout,re.I), 'LED inactive transition not observed'
    results[case]={'uart_expected':expected,'uart_matched':True,'p4_fe_ff_observed':True}
    print(case,': PASS')
results['scope']='C52 instruction model, ideal XRAM and UART; P4 raw SFR writes only. Not an exact SAB80535-N or physical board simulation.'
(reports/'firmware-simulation.json').write_text(json.dumps(results,indent=2))
