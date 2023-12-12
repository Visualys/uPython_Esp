# RF Sniffer (ESP32)
# ------------------
from machine import Pin, time_pulse_us
from utime import sleep

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

"""
def read_pulse():
    h = time_pulse_us(RX_PIN, 1, 1000000)
    l = time_pulse_us(RX_PIN, 0, 1000000)
    aggr = 100
    h = aggr * int(h / aggr)
    l = aggr * int(l / aggr)
    return h,l
    
def read_rf():
    valid = False
    while not valid:
        dat = []
        h=l=0
        while not 15000 < l < 17000:
            h,l = read_pulse()
        valid = True
        l=0
        while not 15000 < l < 17000:
            h,l = read_pulse()
            dat.append(l)
            if (5 < len(dat) < 45) and not (500 < l < 5000): 
                valid = False
                break
            if len(dat)>46:
                valid = False
                break                
    if len(dat)==46:
        out=''
        n=5
        while n < len(dat):
            if dat[n]>3000:
                out+='1'
            else:
                out+='0'
            n+=1
        try:
            temp1=eval('0b' + out[18:24])-15
            temp2=eval('0b' + out[24:28])
            #if temp2>10:
            #    temp2=10-temp2
            temp2=temp2/16
            hum=eval('0b' + out[28:36])
            #print (dat, out)
            print('%s°C %x%s' % (temp1+temp2, hum, '%H'))
        except:
            pass

def read_rf_loop():
    while True:
        read_rf()
"""        
import _thread

start_wifi()
#_thread.start_new_thread(read_rf_loop, ())

# ------------------------------ new version

def rf_read_pulse(pulselength=0):
    h = time_pulse_us(RX_PIN, 1, 1000000)
    l = time_pulse_us(RX_PIN, 0, 1000000)
    if pulselength == 0:
        pulselength = h if h > 0 else 1
    return pulselength , [round(h/pulselength),round(l/pulselength)]

def rf_sniff():
    valid = False
    while not valid:
        dat=[]
        while not valid:
            ret = rf_read_pulse()
            if ret[0] > 100 and ret[1][1]>8:
                valid = True                
        pulselength = ret[0]
        longpulse = ret[1][1]
        for n in range(99):
            ret = rf_read_pulse(pulselength)
            if 0 in ret[1]:
                valid = False
                break
            if ret[1][1]>=longpulse:
                break
            dat.append(ret[1])
        if n<8:
            valid = False
        if valid:
            return pulselength, dat

def decode1(ret):
    c = ''
    pmin = 999
    pmax = 0
    for n in range(len(ret[1])):
        if ret[1][n][1] < pmin:
            pmin = ret[1][n][1]
        if ret[1][n][1] > pmax:
            pmax = ret[1][n][1]
    pavg = (pmin+pmax)/2        
    for n in range(len(ret[1])):
        c+='1' if ret[1][n][1]/ret[1][n][0]>pavg else '0'
    if len(c)==40:
        print(c)
        temp = round((eval('0b'+c[16:28])-1220)*(1/18),2)
        hum = '%x' % eval('0b' + c[28:36]) 
        ch = eval('0b' + c[36:40])
        print( 'temperature:%s, humidity:%s, channel:%s' %(temp, hum, ch))
        sleep(0.25)
    

def loop2():
    while True:
        a = rf_sniff()
        decode1(a)

#----------------------------------------- version 2023-12-12
def rf_read_pulse():
    h = time_pulse_us(RX_PIN, 1, 100000)
    l = time_pulse_us(RX_PIN, 0, 100000)
    if h==0:
        h=1
    return h, round(4*(l/h)) # pulselength, count of low quartets

def rf_sniff():
    minlength = 128
    minsyncquartet = 80
    maxdata = 99
    tim = []
    dat = []
    count = 0
    valid = False
    while not valid:
        pulselength, quartet = rf_read_pulse()
        if pulselength > minlength and quartet > minsyncquartet: # sync detection
            valid = True
            longpulse = quartet
    tim.append(pulselength)
    dat.append(quartet)
    while valid:
        pulselength, quartet = rf_read_pulse()
        if pulselength < minlength or quartet < 1:
            valid = False
            break
        count += 1
        tim.append(pulselength)
        dat.append(quartet)
        if .78*longpulse < quartet < 1.22*longpulse:
            break
        if count > maxdata:
            valid = False
            break
    if count < 10:
        valid = False
    return valid, tim, dat

def rf_decode(tim, dat):
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
    print('occur1:%s, occur2:%s, removed %s' % (occur1, occur2, head_removed))
    avg = .5 * (occur1 + occur2)
    for t in dat[:-1]:
        out += '1' if t > avg else '0'
    print(out)
    if len(out)==24 and len(head_removed)==1:
        print('detected SCS !')
    if len(out)==40 and len(head_removed)==6:
        print('detected TFA Dostmann !')
        temp = round((eval('0b'+out[16:28])-1220)*(1/18),2)
        hum = '%x' % eval('0b' + out[28:36]) 
        ch = eval('0b' + out[36:40])
        print( 'temperature:%s, humidity:%s, channel:%s' %(temp, hum, ch))
        sleep(0.25)
    if len(out)==64 and len(head_removed)==2:
        print('detected Smartwares !')

def loop_sniff():
    while True:
        valid, tim, dat = rf_sniff()
        if valid:
            print('timing:')
            print(tim)
            print('data:')
            print(dat)
            rf_decode(tim, dat)

