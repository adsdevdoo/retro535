/* retro535 bring-up, SDCC mcs51, 11.0592 MHz, UART 9600 8N1.
 * SFR addresses verified against Siemens SAB80515/80535, table 1 pp46-48.
 * All variables and the stack are INTERNAL; SRAM test destroys all XDATA.
 */
#include <stdint.h>
__sfr __at(0x87) PCON;
__sfr __at(0x88) TCON;
__sfr __at(0x89) TMOD;
__sfr __at(0x8a) TL0;
__sfr __at(0x8b) TL1;
__sfr __at(0x8c) TH0;
__sfr __at(0x8d) TH1;
__sfr __at(0x98) SCON;
__sfr __at(0x99) SBUF;
__sfr __at(0xa8) IEN0;
__sfr __at(0xb8) IEN1;
__sfr __at(0xe8) P4;
__sbit __at(0x8c) TR0;
__sbit __at(0x8d) TF0;
__sbit __at(0x8e) TR1;
__sbit __at(0x99) TI;
__sbit __at(0xe8) LED_N;
volatile __data uint8_t test_status; /* 0=busy, 0xa5=pass, 0xe1=fail */
volatile __data uint16_t fail_address;
volatile __data uint8_t fail_expected, fail_actual;
#define RAM ((volatile __xdata uint8_t *)0x0000)
#define RAM_SIZE 0x8000u

static void putc_uart(char c) { SBUF=c; while(!TI) {} TI=0; }
static void puts_uart(const char __code *s) { while(*s) putc_uart(*s++); }
static void hex8(uint8_t n) {
    const char __code digits[]="0123456789ABCDEF";
    putc_uart(digits[n>>4]); putc_uart(digits[n&15]);
}
static uint8_t check(uint16_t a,uint8_t expected) {
    uint8_t actual=RAM[a];
    if(actual==expected) return 1;
    fail_address=a; fail_expected=expected; fail_actual=actual; return 0;
}
/* Debugger landmarks: allow reproducible fault injection, no simulation I/O. */
void address_verify_start(void) { __asm nop __endasm; }
void tests_complete(void) { __asm nop __endasm; }

static uint8_t sram_test(void) {
    uint16_t a;
    uint8_t bit;
    /* Walking ones and zeros exercise every data pin. */
    for(bit=1;bit;bit<<=1) {
        RAM[0]=bit; if(!check(0,bit)) return 0;
        RAM[0]=(uint8_t)~bit; if(!check(0,(uint8_t)~bit)) return 0;
    }
    /* Address-derived signature detects common address aliases. */
    for(a=0;a<RAM_SIZE;++a) RAM[a]=(uint8_t)(a^(a>>8));
    address_verify_start();
    for(a=0;a<RAM_SIZE;++a) if(!check(a,(uint8_t)(a^(a>>8)))) return 0;
    /* March C-: up(w0), up(r0,w1), up(r1,w0),
       down(r0,w1), down(r1,w0), up(r0), whole 32 KiB. */
    for(a=0;a<RAM_SIZE;++a) RAM[a]=0;
    for(a=0;a<RAM_SIZE;++a) { if(!check(a,0)) return 0; RAM[a]=0xff; }
    for(a=0;a<RAM_SIZE;++a) { if(!check(a,0xff)) return 0; RAM[a]=0; }
    a=RAM_SIZE;
    while(a) { --a; if(!check(a,0)) return 0; RAM[a]=0xff; }
    a=RAM_SIZE;
    while(a) { --a; if(!check(a,0xff)) return 0; RAM[a]=0; }
    for(a=0;a<RAM_SIZE;++a) if(!check(a,0)) return 0;
    return 1;
}
static void delay_50ms(void) {
    TR0=0; TF0=0; TH0=0x4c; TL0=0x00;
    /* 65536 - 46080; timer clock = 11059200/12 Hz. */
    TR0=1; while(!TF0) {} TR0=0; TF0=0;
}
void main(void) {
    uint8_t i,ok;
    IEN0=0; IEN1=0; P4=0xff; test_status=0;
    PCON &= 0x7f; /* SMOD=0, preserve other bits. */
    TMOD=0x21; TCON=0; TH1=0xfd; TL1=0xfd; SCON=0x50; TR1=1;
    puts_uart("\r\nretro535 v1.0 | SAB80535-N | 9600 8N1\r\n");
    puts_uart("SRAM 0000-7FFF: testing (destructive)...\r\n");
    ok=sram_test();
    if(ok) { test_status=0xa5; puts_uart("SRAM PASS 32768 bytes\r\n"); }
    else {
        test_status=0xe1; puts_uart("SRAM FAIL @");
        hex8(fail_address>>8); hex8(fail_address);
        puts_uart(" expected="); hex8(fail_expected);
        puts_uart(" actual="); hex8(fail_actual); puts_uart("\r\n");
    }
    puts_uart("LED P4.0: slow=PASS, fast=FAIL. RESET repeats test.\r\n");
    tests_complete();
    while(1) {
        LED_N=!LED_N;
        for(i=0;i<(ok?10:2);++i) delay_50ms();
    }
}
