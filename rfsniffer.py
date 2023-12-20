# RF Sniffer (ESP32)
# ------------------
from machine import Pin, time_pulse_us
from utime import sleep
import urequests

HOSTNAME = 'ESP_RF_SNIFFER'
RX_PIN = Pin(13, Pin.IN)

# Wifi Connection :
sta = None
def start_wifi(ssid='Ben&Steph', pwd='Ben&Steph'):
    global sta
    import network
    from utime import sleep
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
            sleep(0.25)
            timeout += 0.25
            if timeout >= 12:
                import machine
                machine.reset()
        print()
        print('rssi: %sdB IP: %s' % (sta.status('rssi'),sta.ifconfig()[0]))


#----------------------------------------- version 2023-12-19
def rf_read_pulse():
    h = time_pulse_us(RX_PIN, 1, 100000)
    l = time_pulse_us(RX_PIN, 0, 100000)
    return h, l

def rf_sniff():
    detectH = 100
    detectL = 9500
    maxdata = 99
    dat = []
    count = 0
    valid = False
    while not valid:
        h, l = rf_read_pulse()
        if h > detectH and l > detectL: # sync detection
            valid = True
            longlow = l
    dat.append(h)
    dat.append(l)
    while valid:
        h, l = rf_read_pulse()
        if h < detectH or l < detectH:
            valid = False
            break
        count += 1
        dat.append(h)
        dat.append(l)
        tolerance = longlow * 0.22
        if (longlow-tolerance) < l < (longlow+tolerance):
            break
        if count > maxdata:
            valid = False
            break
    if count < 10:
        valid = False
    print(valid, dat)
    return valid, dat

def loop():
    while True:
        valid = False
        while not valid:
            valid, dat = rf_sniff()
        aggregate=1
        while len(set(dat))>6:
            aggregate*=2
            for n in range(len(dat)):
                dat[n]=aggregate*round(dat[n]/aggregate)
        print(dat)
        if min(dat)>0:
            sig = list(set(dat))
            sig.sort()
            req = '&sig=' + ','.join(str(n) for n in sig)
            req+='&seq=' + ''.join(str(sig.index(n)) for n in dat)
            print(req)
            urequests.get('http://192.168.1.32:8080/dmx?cmd=rfrec'+req)
            T = [int(4*dat[n+1]/dat[n]) for n in range(0, len(dat), 2)]
            print(T)
            rf_decode(T)

def rf_decode(dat):
    out = ''
    head_removed = []
    frequencies = sorted(dat,key=dat.count, reverse=True)
    occur1 = frequencies[0]
    for n in range(len(frequencies)):
        if abs(frequencies[n] - occur1)>2:
            occur2=frequencies[n]
            break
    while True:
        if (-5 <= (occur1-dat[0]) <= 5) or (-5 <= (occur2-dat[0]) <= 5):
            break
        head_removed.append(dat[0])
        dat = dat[1:]
    avg = .5 * (occur1 + occur2)
    for t in dat[:-1]:
        out += '1' if t > avg else '0'
    if len(out)==24 and len(head_removed)==1:
        print('detected SCS !')
        print(out)
    elif len(out)==40 and len(head_removed)==6:
        print('detected TFA Dostmann !')
        print(out)
        idx = eval('0b' + out[0:8]) 
        temp = round((eval('0b'+out[16:28])-1220)*(1/18),2)
        hum = '%x' % eval('0b' + out[28:36]) 
        ch = eval('0b' + out[36:40])
        print( 'id:%s, temperature:%s, humidity:%s, channel:%s' %(idx, temp, hum, ch))
        sleep(0.4)
    elif len(out)==64 and len(head_removed)==2:
        print('detected Smartwares !')
        print(out)
    else:
        print(dat)
        print('occur1:%s, occur2:%s, removed %s' % (occur1, occur2, head_removed))
        print(out)

import _thread
start_wifi()
#_thread.start_new_thread(read_rf_loop, ())
loop()

