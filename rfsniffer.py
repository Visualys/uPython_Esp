# RF Sniffer (ESP32)
# ------------------
from machine import Pin, time_pulse_us

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
        
import _thread

start_wifi()
#_thread.start_new_thread(read_rf_loop, ())

# ------------------------------ new version

def read_pulse2(pulselength=1):
    h = time_pulse_us(RX_PIN, 1, 1000000)
    l = time_pulse_us(RX_PIN, 0, 1000000)
    if pulselength == 1:
        pulselength = h if h > 0 else 1
    return pulselength , [round(h/pulselength),round(l/pulselength)]

def find1():
    valid = False
    while not valid:
        dat=[]
        while not valid:
            ret = read_pulse2()
            if ret[0] > 100 and ret[1][1]>10:
                valid = True                
        pulselength = ret[0]
        longpulse = ret[1][1]
        #dat.append(ret[1])
        for n in range(99):
            ret = read_pulse2(pulselength)
            if 0 in ret[1]:
                valid = False
                break
            if ret[1][1]>=longpulse:
                break
            dat.append(ret[1])
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
        temp = eval('0b' + c[16:28])
        temp2 = round((temp-1220)*(1/18),1)
        hum = '%x' % eval('0b' + c[28:36]) 
        ch = eval('0b' + c[36:40])
        print( c, temp, temp2, hum, ch)
    

def loop2():
    while True:
        a = find1()
        decode1(a)

