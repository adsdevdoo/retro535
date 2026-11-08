"""Reviewed electrical connectivity. Physical pin numbers, not generic 8051 mapping.
Run generate.py using Python, then make_board.py using KiCad's Python.
"""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
C=[]
def add(ref,value,fp,pins,xy,sch,page,mpn='',source='',kind='ic',left=None,angle=0):
    # pins: number -> (name, electrical type, net), None net means explicit no-connect
    C.append(dict(ref=ref,value=value,fp=fp,pins={str(k):list(v) for k,v in pins.items()},
                  xy=xy,sch=sch,page=page,mpn=mpn or value,source=source,kind=kind,left=left,angle=angle))
def p(n,typ='passive',net=None):return (n,typ,n if net is None else net)
def two(ref,val,fp,a,b,xy,sch,page,mpn='',kind='r',angle=0):
    add(ref,val,fp,{1:('1','passive',a),2:('2','passive',b)},xy,sch,page,mpn,kind=kind,angle=angle)
RFP='Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder'
CFP='Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder'
SO8='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm'
def res(ref,val,a,b,xy,sch,page=1,mpn='',angle=0):
    codes={'5.1k':'5K1','10k':'10K','47k':'47K','100k':'100K','1k':'1K','2.2k':'2K2','3.3k':'3K3','10':'10R','0':'0R','100':'100R'}
    two(ref,val,RFP,a,b,xy,sch,page,mpn or 'RC0805FR-07'+codes.get(val,val)+'L',angle=angle)
def cap(ref,val,a,xy,sch,page=1,b='GND',angle=0):
    mpns={'100n':'GRM21BR71H104KA01L','1u':'GRM21BR71C105KA01L','4.7u':'GRM21BR61C475KA73L','30p':'GRM2165C1H300JA01D'}
    two(ref,val,CFP,a,b,xy,sch,page,mpns[val],kind='c',angle=angle)

SAB='https://www.ardent-tool.com/datasheets/Siemens_SAB80515_80535.pdf'
cpu={}
for bit,pin in enumerate([1,2,3,5,6,7,8,9]):cpu[pin]=p('P4_'+str(bit),'bidirectional')
cpu.update({4:('VPD','power_in','GND'),10:('RESET_N','input','RESET_N'),11:('VAREF','power_in','AVREF'),12:('VAGND','power_in','GND')})
for pin in range(13,21):cpu[pin]=p('AN'+str(20-pin),'input')
for bit,pin in enumerate(range(21,29)):
    net=['RXD','TXD','P3_2_INT0_N','P3_3_INT1_N','P3_4_T0','P3_5_T1','WR_N','RD_N'][bit]
    cpu[pin]=(f'P3.{bit}/'+net,'bidirectional',net)
for pin in range(29,37):cpu[pin]=p('P1_'+str(36-pin),'bidirectional')
cpu.update({37:('VBB','passive','VBB'),38:('VSS','power_in','GND'),39:('XTAL2','output','XTAL2'),40:('XTAL1','input','XTAL1')})
for bit in range(8):cpu[41+bit]=(f'P2.{bit}/A{8+bit}','bidirectional',f'A{8+bit}')
cpu.update({49:('PSEN_N','output','PSEN_N'),50:('ALE','output','ALE'),51:('EA_N','input','GND')})
for bit in range(8):cpu[52+bit]=(f'P0.{bit}/AD{bit}','bidirectional',f'D{bit}')
for pin in range(60,68):cpu[pin]=p('P5_'+str(67-pin),'bidirectional')
cpu[68]=('VCC','power_in','+5V')
add('U1','SAB80535-N','Retro535:PLCC68_PreciDip_540-99-068-24-000-1',cpu,(29,26),(98,105),2,source=SAB,left=list(range(1,37)))

latch={1:('OE_N','input','GND'),10:('GND','power_in','GND'),11:('LE','input','ALE'),20:('VCC','power_in','+5V')}
for b in range(8):latch[2+b]=(f'D{b}','input',f'D{b}');latch[19-b]=(f'Q{b}','output',f'A{b}')
add('U2','74HCT573','Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm',latch,(53,29),(75,70),3,'SN74HCT573DWR','https://www.ti.com/lit/ds/symlink/sn74hct573.pdf',left=[2,3,4,5,6,7,8,9,11,1])
flash={1:('NC','no_connect',None),2:('A16','input','GND'),3:p('A15','input'),4:p('A12','input'),16:('VSS','power_in','GND'),22:('CE_N','input','GND'),24:('OE_N','input','PSEN_N'),29:p('A14','input'),30:('NC','no_connect',None),31:('WE_N','input','+5V'),32:('VDD','power_in','+5V')}
for pin,b in zip(range(5,13),range(7,-1,-1)):flash[pin]=p(f'A{b}','input')
for pin,b in zip([13,14,15,17,18,19,20,21],range(8)):flash[pin]=p(f'D{b}','bidirectional')
for pin,b in [(23,10),(25,11),(26,9),(27,8),(28,13)]:flash[pin]=p(f'A{b}','input')
add('U3','SST39SF010A-70-4C-PHE','Package_DIP:DIP-32_W15.24mm_Socket_LongPads',flash,(62,23),(185,90),3,source='https://ww1.microchip.com/downloads/aemDocuments/documents/MPD/ProductDocuments/DataSheets/SST39SF010A-SST39SF020A-SST39SF040-Data-Sheet-DS20005022.pdf',left=[*range(2,13),23,25,26,27,28,29])
sram={1:p('A14','input'),2:p('A12','input'),14:('VSS','power_in','GND'),20:('CE_N','input','A15'),22:('OE_N','input','RD_N'),26:p('A13','input'),27:('WE_N','input','WR_N'),28:('VCC','power_in','+5V')}
for pin,b in zip(range(3,11),range(7,-1,-1)):sram[pin]=p(f'A{b}','input')
for pin,b in zip([11,12,13,15,16,17,18,19],range(8)):sram[pin]=p(f'D{b}','bidirectional')
for pin,b in [(21,10),(23,11),(24,9),(25,8)]:sram[pin]=p(f'A{b}','input')
add('U4','AS6C62256A-70PCN','Package_DIP:DIP-28_W15.24mm_Socket_LongPads',sram,(83,23),(300,90),3,source='https://www.alliancememory.com/wp-content/uploads/AS6C62256A-70PCN_AS6C62256A.pdf',left=[1,2,3,4,5,6,7,8,9,10,21,23,24,25,26])

usb={}
for n in ['A1','A12','B1','B12','S1']:usb[n]=(n,'passive','GND')
for n in ['A4','A9','B4','B9']:usb[n]=(n,'passive','VBUS')
for n in ['A6','B6']:usb[n]=(n,'passive','USB_DP')
for n in ['A7','B7']:usb[n]=(n,'passive','USB_DM')
for n in ['A5','B5']:usb[n]=(n,'passive','CC1' if n=='A5' else 'CC2')
for n in ['A8','B8']:usb[n]=(n,'no_connect',None)
add('J1','USB-C','Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12',usb,(12,4),(48,66),1,'TYPE-C-31-M-12','https://datasheet.lcsc.com/datasheet/pdf/9e56b777c022540fcce7c7f67825f55e.pdf')
res('R1','5.1k','CC1','GND',(6,10),(45,111))
res('R2','5.1k','CC2','GND',(18,10),(45,127))
two('F1','0.75A PTC','Fuse:Fuse_1812_4532Metric','VBUS','VBUS_F',(25,5),(120,38),1,'MF-MSMF075-2',kind='fuse')
two('FB1','600R@100MHz','Inductor_SMD:L_0805_2012Metric_Pad1.15x1.40mm_HandSolder','VBUS_F','+5V_USB',(32,5),(185,38),1,'BLM21PG601SN1D',kind='r')
cap('C1','4.7u','+5V_USB',(29,10),(250,38))
cap('C2','100n','VBUS',(20,5),(315,38))
esd={1:('IO1','passive','USB_DP'),2:('GND','power_in','GND'),3:('IO2','passive','USB_DM'),4:('IO2','passive','USB_DM'),5:('VBUS','power_in','VBUS'),6:('IO1','passive','USB_DP')}
add('D1','USBLC6-2SC6','Package_TO_SOT_SMD:SOT-23-6',esd,(12,10),(47,165),1,source='https://www.st.com/resource/en/datasheet/usblc6-2.pdf')
ft={1:('TXD','output','FT_TX'),2:('DTR_N','output',None),3:('RTS_N','output',None),4:('VCCIO','power_in','+5V_USB'),5:('RXD','input','FT_RX'),6:('RI_N','input','+5V_USB'),7:('GND','power_in','GND'),8:('NC','no_connect',None),9:('DSR_N','input','+5V_USB'),10:('DCD_N','input','+5V_USB'),11:('CTS_N','input','GND'),12:('CBUS4','output',None),13:('CBUS2','output',None),14:('CBUS3/PWREN_N','output','PWREN_N'),15:('USBDP','bidirectional','USB_DP'),16:('USBDM','bidirectional','USB_DM'),17:('3V3OUT','power_out','FT_3V3'),18:('GND','power_in','GND'),19:('RESET_N','input','+5V_USB'),20:('VCC','power_in','+5V_USB'),21:('GND','power_in','GND'),22:('CBUS1','output',None),23:('CBUS0','output',None),24:('NC','no_connect',None),25:('AGND','power_in','GND'),26:('TEST','input','GND'),27:('OSCI','input',None),28:('OSCO','output',None)}
add('U5','FT232RL','Package_SO:SSOP-28_5.3x10.2mm_P0.65mm',ft,(14,20),(145,95),1,source='https://ftdichip.cn/Support/Documents/DataSheets/ICs/DS_FT232R.pdf',angle=180)
cap('C3','100n','+5V_USB',(20,23),(105,148))
cap('C4','100n','+5V_USB',(8,23),(170,148))
cap('C5','100n','FT_3V3',(20,17),(235,148))
power={1:('GND','power_in','GND'),2:('IN','power_in','+5V_USB'),3:('IN','power_in','+5V_USB'),4:('EN_N','input','EN_N'),5:('OC_N','open_collector','OC_N'),6:('OUT','power_out','+5V'),7:('OUT','passive','+5V'),8:('OUT','passive','+5V')}
add('U6','TPS2041BDR',SO8,power,(37,10),(265,87),1,source='https://www.ti.com/lit/ds/symlink/tps2041b.pdf')
res('R3','10k','+5V_USB','PWREN_N',(25,17),(330,68))
res('R4','10k','+5V_USB','EN_N',(44,10),(330,84))
two('JP1','RUN - FIT AFTER FT_PROG','Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical','PWREN_N','EN_N',(47,5),(330,110),1,'M20-9990245',kind='jumper',angle=90)
res('R5','10k','+5V_USB','OC_N',(44,16),(330,132))
cap('C6','100n','+5V_USB',(33,15),(300,165))
cap('C7','4.7u','+5V',(39,16),(365,165))
cap('C8','100n','+5V',(43,22),(365,186))
res('R6','2.2k','+5V','PWR_LED_A',(54,5),(110,190))
two('D2','POWER green','LED_SMD:LED_0805_2012Metric_Pad1.15x1.40mm_HandSolder','GND','PWR_LED_A',(59,5),(175,190),1,'LTST-C170KGKT',kind='led')

# Reset, oscillator and analogue reference. CPU VBB is capacitive only.
reset={1:('RESET_N','open_collector','RESET_N'),2:('VDD','power_in','+5V'),3:('NC','no_connect',None),4:('VSS','power_in','GND'),5:('NC','no_connect',None),6:('NC','no_connect',None),7:('NC','no_connect',None),8:('NC','no_connect',None)}
add('U7','MCP120-475I/SN',SO8,reset,(12,33),(240,65),2,source='https://ww1.microchip.com/downloads/en/DeviceDoc/11184D.pdf')
res('R7','10k','+5V','RESET_N',(10,39),(315,55),2)
two('SW1','RESET','Button_Switch_THT:SW_PUSH_6mm','RESET_N','GND',(4,44),(315,80),2,'B3F-1000',kind='switch')
cap('C9','100n','+5V',(17,33),(315,105),2)
two('Y1','11.0592MHz CL20p','Crystal:Crystal_HC49-U_Vertical','XTAL2','XTAL1',(32,58),(240,140),2,'ECS-110.5-20-4X',kind='crystal')
C[-1]['source']='https://www.ecsxtal.com/store/pdf/hc-49usx.pdf'
cap('C10','30p','XTAL1',(34,53),(305,134),2)
cap('C11','30p','XTAL2',(38,55),(305,151),2)
cap('C12','100n','VBB',(29,54),(240,180),2)
cap('C13','100n','+5V',(33,24),(240,205),2)
cap('C14','1u','+5V',(37,24),(305,205),2)
res('R8','10','+5V','AVREF',(11,29),(240,235),2)
cap('C15','100n','AVREF',(10,27),(305,225),2)
cap('C16','1u','AVREF',(6,27),(305,242),2)
# Analog inputs default weakly grounded; headers can drive 0..AVREF.
for i in range(8):res(f'R{20+i}','100k',f'AN{i}','GND',(5+(i%2)*4,52+(i//2)*4),(50+85*(i%2),180+19*(i//2)),2)
cap('C17','100n','+5V',(53,20),(75,135),3)
cap('C18','100n','+5V',(77,20),(185,150),3)
cap('C19','100n','+5V',(97,20),(300,150),3)
res('R9','10k','+5V','WR_N',(49,54),(75,167),3)
res('R10','10k','+5V','RD_N',(49,58),(75,184),3)

# UART isolation: always powered TTL buffers. RESET_N low => outputs disabled.
buf={1:('1OE_N','input','UART_OE_N'),2:('1A','input','FT_TX'),3:('1Y','tri_state','UART_RX_BUF'),4:('2OE_N','input','UART_OE_N'),5:('2A','input','TXD'),6:('2Y','tri_state','FT_RX'),7:('GND','power_in','GND'),8:('3Y','tri_state',None),9:('3A','input','GND'),10:('3OE_N','input','+5V_USB'),11:('4Y','tri_state',None),12:('4A','input','GND'),13:('4OE_N','input','+5V_USB'),14:('VCC','power_in','+5V_USB')}
add('U8','74AHCT125','Package_SO:SOIC-14_3.9x8.7mm_P1.27mm',buf,(25,19),(70,65),4,'SN74AHCT125DR','https://www.ti.com/lit/ds/symlink/sn74ahct125.pdf')
add('Q1','MMBT3904','Package_TO_SOT_SMD:SOT-23',{1:('B','input','UART_BASE'),2:('E','passive','GND'),3:('C','open_collector','UART_OE_N')},(27,25),(155,60),4)
res('R11','47k','RESET_N','UART_BASE',(24,29),(155,90),4)
res('R12','10k','+5V_USB','UART_OE_N',(28,12),(155,110),4)
res('R13','100k','UART_BASE','GND',(27,32),(155,130),4)
cap('C20','100n','+5V_USB',(29,18),(70,105),4)
res('R15','100k','TXD','GND',(56,50),(155,151),4)
two('JP2','USB RX LINK','Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical','UART_RX_BUF','RXD',(22,36),(70,135),4,'M20-9990245',kind='jumper')
res('R14','3.3k','+5V','USER_LED_A',(17,61),(70,164),4)
two('D3','USER P4.0 active LOW','LED_SMD:LED_0805_2012Metric_Pad1.15x1.40mm_HandSolder','P4_0','USER_LED_A',(22,61),(155,164),4,'LTST-C170KRKT',kind='led')

def header(ref,desc,nets,xy,sch,angle=90):
    # dual row: 1,2 at first column; 3,4 next ...
    n=len(nets);rows=n//2
    add(ref,desc,f'Connector_PinHeader_2.54mm:PinHeader_2x{rows:02}_P2.54mm_Vertical',
        {i+1:(net,'passive',net) for i,net in enumerate(nets)},xy,sch,4,'M20-998'+str(rows).zfill(2)+'46',kind='header',angle=angle)
header('J2','P1',[f'P1_{i}' for i in range(8)]+['+5V','GND'],(15,73),(250,50))
header('J3','P4',[f'P4_{i}' for i in range(8)]+['+5V','GND'],(33,73),(330,50))
header('J4','P5',[f'P5_{i}' for i in range(8)]+['+5V','GND'],(50,73),(250,90))
header('J5','ANALOG',[f'AN{i}' for i in range(8)]+['AVREF','GND'],(4,55),(330,90),angle=0)
header('J6','P3 / UART',['RXD','TXD','P3_2_INT0_N','P3_3_INT1_N','P3_4_T0','P3_5_T1','RESET_N','GND'],(68,73),(250,130))
header('J7','BUS RESERVED',['D0','D1','D2','D3','D4','D5','D6','D7','A0','A1','A2','A3','A4','A5','A6','A7','A8','A9','A10','A11','A12','A13','A14','A15','PSEN_N','ALE','RD_N','WR_N','+5V','GND'],(59,12),(330,175))

for i,(net,xy) in enumerate([('GND',(94,5)),('+5V_USB',(89,5)),('+5V',(84,5)),('RESET_N',(19,42)),('ALE',(49,47)),('PSEN_N',(49,50)),('RD_N',(54,53)),('WR_N',(54,57)),('AVREF',(10,48)),('OC_N',(44,19))],1):
    add('TP'+str(i),net,'TestPoint:TestPoint_Pad_D2.0mm',{1:(net,'passive',net)},xy,([40,105,170,235,370][(i-1)%5],222+(i-1)//5*18),4,'PCB test pad',kind='tp')

# Power-source declarations for ERC. No footprint. These declare actual sources only.
for i,net in enumerate(['GND','VBUS','+5V_USB','AVREF'],1):
    add('#FLG'+str(i),'PWR_FLAG','',{1:(net,'power_out',net)},(0,0),(35+90*(i-1),245),1,'',kind='flag')

if __name__=='__main__':
    (ROOT/'hardware/design.json').write_text(json.dumps(C,indent=2),encoding='utf-8')
