from machine import Pin, UART
import machine
from utime import sleep
import gc

led = Pin(2, Pin.OUT)

# Wifi Connection :
sta = None
def start_wifi(ssid='Ben&Steph'):
    global sta
    import network
    from time import sleep 
    if sta is None:
        sta = network.WLAN(network.STA_IF)
        sta.active(False)
        sta.active(True)
    if not sta.isconnected():
        sta.connect(ssid, 'Ben&Steph')
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

# Send to DMX webserver
def send_to_server(d):
    import usocket
    s = usocket.socket()
    try:
        s.connect(('192.168.1.32',8080))
    except OSError:
        return 0
    s.setblocking(False)
    ret = s.send(bytes('GET /dmx?mes={} HTTP/1.1\r\n\r\n\r\n'.format(','.join(d)), 'utf8'))
    s.close()
    return ret

# startup delay
print('start in 3s...')
sleep(3)


# Modbus connection :
# GPIO4 -> DE/DE
# GPIO18 -> DI
# GPIO19 -> RO
ctrl_tx = Pin(4, Pin.OUT)
ctrl_tx(0)
host = UART(2)
host.init(baudrate=115200, bits=8, parity=None, stop=1, rx=18, tx=19, timeout=1000)
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
status = 0
volt = 0
freq = 0
batload = 0
batlev = 0
powedfin = 0
powload = 0
powme3000 = 0
powpv = 0
todaypv = 0
todayedfout = 0
todayedfin = 0
todayload = 0
batcycles = 0
    
def read_me3000sp():
    global status, volt, freq, batload, batlev, powedfin, powload, powme3000, powpv,todaypv,todayedfout,todayedfin,todayload,batcycles
    a = [1, 3, 0x02, 0x00, 0, 45]
    a+=crc16(a)
    ctrl_tx(1)
    host.write(bytes(a))
    host.flush()
    ctrl_tx(0)
    r = host.read()
    i=3
    status = statxt[r[i]<<8 | r[i+1]]
    i+=12
    volt = (r[i]<<8 | r[i+1]) * .1
    i+=12
    freq = (r[i]<<8 | r[i+1]) * .01
    i+=2
    batload = -signedinteger((r[i], r[i+1])) * 10
    i+=6
    batlev = (r[i]<<8 | r[i+1])
    i+=4
    powedfin = -signedinteger((r[i], r[i+1])) * 10
    i+=2
    powload = (r[i]<<8 | r[i+1]) * 10
    i+=2
    powme3000 = signedinteger((r[i], r[i+1])) * 10
    i+=2
    powpv = (r[i]<<8 | r[i+1]) * 10
    i+=6
    todaypv = (r[i]<<8 | r[i+1]) * 10
    i+=2
    todayedfout = (r[i]<<8 | r[i+1]) * 10
    i+=2
    todayedfin = (r[i]<<8 | r[i+1]) * 10
    i+=2
    todayload = (r[i]<<8 | r[i+1]) * 10
    i+=34
    batcycles = r[i]<<8 | r[i+1]

def run():
    gc.collect()
    start_wifi()
    led(1)
    read_me3000sp()
    led(0)
    dic = ['25', str(batlev),'26', status, '27', str(powme3000),'28', str(todaypv),'29', str(todayedfin),'30', str(todayload),'31', str(powpv),'32', str(powedfin),'33', str(powload), '34', str(todayedfout)]
    send_to_server(dic)

def autorun():
    while True:
        run()
        sleep(3)

autorun()
