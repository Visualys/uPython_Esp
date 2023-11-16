from machine import Pin, SPI
spi = SPI(1, baudrate=1000000, polarity=0, phase=0)
rf24_ce = Pin(16, Pin.OUT)
rf24_cs = Pin(15, Pin.OUT)
rf24_status=0

from utime import sleep_ms

def rf24_command(cmd):
    global rf24_status
    rf24_status = spi.read(1, cmd)[0]
    
def rf24_readbyte():
    return spi.read(1)[0]

def rf24_writebyte(value):
    byte = bytes([value])
    spi.write(byte)

def rf24_reg_read(reg):
    rf24_cs(0)
    rf24_command(reg)
    rx = rf24_readbyte()
    rf24_cs(1)
    return rx

def rf24_reg_write(reg, byte):
    rf24_cs(0)
    rf24_command(0x20 | reg)
    rf24_writebyte(byte)
    rf24_cs(1)

def rf24_setconfig(freq, speed, power):
    buf=0
    if(speed==0):
        buf = 0b00100000                       # 250kpbs
    elif(speed==1):
        buf = 0b00000000                       # 1Mbps
    else:
        buf = 0b00001000                       # 2Mbps
    buf |= ((power&3) << 1);
    rf24_reg_write(0x06, buf)                  # RF_SETUP
    rf24_reg_write(0x05, freq)                 # RF_CH
    
def rf24_setautoretransmit(delay, count):
    buf=0
    buf = (delay << 4) | (count & 0x0F)
    rf24_reg_write(4,buf)

def rf24_setaddress(pipe, a5, a4, a3, a2, a1):
    rf24_cs(0)
    rf24_command(0x20 | 0x0A | pipe)
    rf24_writebyte(a1)
    if(pipe<2):
        rf24_writebyte(a2)
        rf24_writebyte(a3)
        rf24_writebyte(a4)
        rf24_writebyte(a5)
    rf24_cs(1)
    if(pipe==0):
        rf24_cs(0)
        rf24_command(0x20 | 0x10)
        rf24_writebyte(a1)
        rf24_writebyte(a2)
        rf24_writebyte(a3)
        rf24_writebyte(a4)
        rf24_writebyte(a5)
        rf24_cs(1)

def rf24_set_payload_length(l):
    for n in range(6):
        rf24_reg_write(0x11 + n, l)

def rf24_clear_status():
    rf24_reg_write(0x07, 0b01110000)

def rf24_flush():
    rf24_cs(0)
    rf24_command(0b11100010)   # Flush RX
    rf24_cs(1)
    rf24_cs(0)
    rf24_command(0b11100001)   # Flush TX
    rf24_cs(1)

def rf24_powerup_rx():
    rf24_reg_write(0x07, 0b01110000) # Clear STATUS
    rf24_flush()
    rf24_reg_write(0x00, ((rf24_reg_read(0x00) & 0b11111100)) | 0b00000011)
    rf24_ce(1)
    sleep_ms(10)
    
def rf24_powerup_tx():
    rf24_reg_write(0x07, 0b01110000) # Clear STATUS
    rf24_flush()
    rf24_reg_write(0x00, ((rf24_reg_read(0x00) & 0b11111100)) | 0b00000010)
    rf24_ce(1)
    sleep_ms(10)

def rf24_powerdown():
    CONFIG=0
    rf24_reg_write(0x07, 0b01110000) # Clear STATUS
    rf24_flush()
    CONFIG = rf24_reg_read(0x00)
    rf24_reg_write(0x00, (CONFIG & 0b11111100))
    rf24_ce(0)
    sleep_ms(10)

def rf24_getstatus():
    rf24_cs(0)
    rf24_command(0xFF)
    rf24_cs(1)
    return rf24_status

def rf24_dataready():
    if(rf24_getstatus() & 0b01000000):
        return 1
    if(rf24_reg_read(0x17) & 1):
        return 0
    else:
        return 1
    
def rf24_datasent():
    return True if(rf24_getstatus() & 0b00100000) else False

def rf24_maxretry():
    return (rf24_getstatus() & 0b00010000)

def rf24_get_payloadlength():
    buf=0
    rf24_cs(0)
    rf24_command(0b01100000)            # R_RX_PL_WID
    buf = rf24_readbyte()
    rf24_cs(1)
    return buf

def rf24_send(msg):
    rf24_cs(0) 
    rf24_command(0b10100000)            # W_TX_PAYLOAD
    for n in range(len(msg)):
        rf24_writebyte(msg[n])
    rf24_cs(1)  

def rf24_get_message():
    rf24_cs(0)
    rf24_command(0b01100001)            # R_TX_PAYLOAD
    for n in range(32):
        msg[n]=rf24_readbyte()
    rf24_cs(1)

def rf24_init():
    rf24_ce(0)
    rf24_cs(1)
    sleep_ms(200)
    rf24_setconfig(90, 0, 3)
    rf24_setaddress(0, 100,100,100,100,100)
    rf24_setautoretransmit(15, 15)
    rf24_set_payload_length(32)

t = b'event,toto=1\n                   '
