from machine import Pin, UART
import machine
from utime import sleep
import gc

MODBUS_RX = 18
MODBUS_TX = 19
MODBUS_DE_RE = 4

led = Pin(2, Pin.OUT)

# Wifi Connection :
sta = None
def start_wifi(ssid='Ben&Steph', pwd='Ben&Steph'):
    global sta
    import network
    from time import sleep
    if sta is None:
        sta = network.WLAN(network.STA_IF)
        sta.active(False)
        sta.active(True)
    if not sta.isconnected():
        sta.connect(ssid, pwd)
        print('wifi connection to %s' % ssid, end='')
        timeout = 0
        while not sta.isconnected():
            print('.', end='')
            sleep(0.25)
            timeout += 0.25
            if timeout >= 12:
                import machine
                machine.reset()
        print()
        print('rssi: %sdB IP: %s' % (sta.status('rssi'),sta.ifconfig()[0]))
start_wifi()

# Send to webserver
def send_to_server(txt):
    import usocket
    s = usocket.socket()
    try:
        s.connect(('192.168.1.32',8080))
    except OSError:
        return 0
    s.setblocking(False)
    ret = s.send(bytes('GET /dmx?mes=%s HTTP/1.1\r\n\r\n\r\n' % txt, 'utf8'))
    s.close()
    return ret

# startup delay
print('start in 3s...')
sleep(3)


# Modbus initialisation :
ctrl_tx = Pin(MODBUS_DE_RE, Pin.OUT)
ctrl_tx(0)
host = UART(2)
host.init(baudrate=115200, bits=8, parity=None, stop=1, rx=MODBUS_RX, tx=MODBUS_TX, timeout=1000)
host.read()

def crc16(data):
    crc = 0xFFFF
    for c in data:
        crc = crc ^ c
        for j in range(8):
            if crc & 0x01:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc = crc >> 1
    return [crc & 0xFF, crc >> 8]

def signedinteger(data):
    n = data[0]<<8 | data[1]
    if(n & 0x8000):
        n = (n & 0x7FFF) - 32767
    return n

statxt = ['Wait','Charge (check)','Charge','Discharge (check)','Discharge','EPS','Fault','Fault']
s = ""

def read_me3000sp():
    global s
    a = [1, 3, 0x02, 0x00, 0, 45]
    a+=crc16(a)
    ctrl_tx(1)
    host.write(bytes(a))
    host.flush()
    ctrl_tx(0)
    led(1)
    r = host.read()
    led(0)
    if len(r)==95: 
        s = ""
        i=3
        s='26,' + statxt[r[i]<<8 | r[i+1]] # status
        i+=12
        s+=',11,' + str((r[i]<<8 | r[i+1]) * .1) # voltage
        i+=12
        s+=',12,' + str((r[i]<<8 | r[i+1]) * .01) # frequency
        i+=8
        s+=',25,' + str(r[i]<<8 | r[i+1]) # batery level
        i+=4
        s+=',32,' + str(-signedinteger((r[i], r[i+1])) * 10) # power grid input
        i+=2
        s+=',33,' + str((r[i]<<8 | r[i+1]) * 10) # power home load
        i+=2
        s+=',27,' + str(signedinteger((r[i], r[i+1])) * 10) # power me3000
        i+=2
        s+=',31,' + str((r[i]<<8 | r[i+1]) * 10) # power pv
        i+=6
        s+=',28,' + str((r[i]<<8 | r[i+1]) * 10) # today pv
        i+=2
        s+=',34,' + str((r[i]<<8 | r[i+1]) * 10) # todayedfout
        i+=2
        s+=',29,' + str((r[i]<<8 | r[i+1]) * 10) # todayedfin
        i+=2
        s+=',30,' + str((r[i]<<8 | r[i+1]) * 10) # todayload
        i+=34
#       s+='**,' + str(r[i]<<8 | r[i+1]) # batcycles
        return 1
    return 0

def run():
    gc.collect()
    start_wifi()
    if read_me3000sp():
        send_to_server(s)

def autorun():
    while True:
        run()
        sleep(3)

autorun()
