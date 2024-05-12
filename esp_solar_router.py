import gc, machine, network, usocket
from wifi_cfg import wifiSSID, wifiKey
from utime import sleep
from machine import Pin, PWM
from pzem004tv3 import pzem004tv3
 
HOSTNAME = 'ESP_SOLAR_ROUTER'
 
# startup delay
print('start in 3s...')
sleep(3)
 
# Wifi Connection :
sta = None
def start_wifi(ssid=wifiSSID, pwd=wifiKey):
    global sta
    if sta is None:
        sta = network.WLAN(network.STA_IF)
        sta.active(False)
        sta.active(True)
    if not sta.isconnected():
        sta.config(dhcp_hostname=HOSTNAME)
        sta.connect(ssid, pwd)
        print('wifi connection to %s' % ssid, end='')
        timeout = 0
        while not sta.isconnected():
            print('.', end='')
            sleep(0.5)
            timeout += 0.25
            if timeout >= 10:
                machine.reset()
        print()
        print('rssi: %sdB IP: %s' % (sta.status('rssi'),sta.ifconfig()[0]))
start_wifi()

# Send to webserver
serveraddr = ('192.168.1.32',8080)
 
def server_command(cmd):
    s = usocket.socket()
    try:
        s.connect(serveraddr)
    except OSError:
        machine.reset()
    s.setblocking(True)
    s.sendall(bytes('GET /dmx?%s HTTP/1.1\r\n\r\n\r\n' % cmd, 'utf8'))
    sleep(.5)
    ret = s.recv(1024).decode('utf-8')
    s.close()
    return ret
   
def server_message(msg):
    s = usocket.socket()
    try:
        s.connect(serveraddr)
    except OSError:
        machine.reset()
    s.setblocking(False)
    ret = s.sendall(bytes('GET /dmx?mes=%s HTTP/1.1\r\n\r\n\r\n' % msg, 'utf8'))
    s.close()
    return ret
 
class servo():
    pin = 0
    p = 0
    amin = 20
    amax = 120
    reverse = False
    percent = 0
    def init(this, pin):
        from machine import Pin, PWM
        this.pin = Pin(pin, Pin.OUT)
        this.p = PWM(this.pin)
        a = this.amax if this.reverse else this.amin
        this.p.duty(a)
        this.p.freq(50)
    def set(this, percent):
        current = this.p.duty()
        destination = 120 - percent if this.reverse else 20 + percent
        step = 1 if current < destination else -1
        while current != destination:
            current += step
            this.p.duty(current)
            sleep(0.03)
        this.percent = percent
s = servo()
s.reverse = True
s.init(17)
s.set(0)

s2 = servo()
s2.reverse = True
s2.init(16)
s2.set(0)

pzem1 = pzem004tv3()
pzem1.init(0x01, 19, 18)


 
w=0
pos = 0
index = 0

def single_process():
    global pos
    batt = 0
    battload=0
    linky=0
    
    c=0
    global w
    gc.collect()
    start_wifi()
    ret = server_command('info_solar_router=1')
    if len(ret):
        ret = [float(x) for x in ret.split(',')]
        for i in range(0, len(ret), 2):
            if ret[i]==25: batt = ret[i+1]
            if ret[i]==27: battload = ret[i+1]
            if ret[i]==32: linky = ret[i+1]
        print('batt:%s battload:%s linky:%s' %(batt,battload,linky))
        if batt<90:
            c=0
        elif battload>0:
            c=0
        else:
            c=w-linky
        print('consigne : %s W' % c)    
        for l in range(4):
            try:
                pzem1.read()
                w=pzem1.watts()
                index=pzem1.index()
                pos+=(c-w)/16
            except:
                pos=0
            if pos>200:pos=200
            if pos<0:pos=0
            #print('w is %s - set pos to %s' % (w,int(pos)))
            if pos<=100:
                s.set(int(pos))
                s2.set(0)
            else:
                s.set(100)
                s2.set(int(pos)-100)
            sleep(1.5)
        server_message('%s,%s,%s,%s,%s,%s' % (20,w,22,pos,21,index) )
 
def run():
    while True:
        single_process()


#run()
import _thread
_thread.start_new_thread(run, ())

