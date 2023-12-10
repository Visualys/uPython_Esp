from machine import Pin, time_pulse_us
from utime import ticks_us
from utime import sleep

CAPTEUR_NUM = 38 # Emetteur Bureau

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

def serve():
    import usocket
    s = usocket.socket()
    s.bind(('0.0.0.0', 80))
    s.listen(1)
    print('waiting for action...')
    while True:
        con, host = s.accept()
        if not sta.isconnected():
            import machine
            machine.reset()
        data = con.recv(1024)
        query = data.decode().split(' ')
        data = ''
        if query[0]=="GET":
            if len(query[1])>2:
                data = query[1][1:].split(',')
                if len(data)==2:
                    print('action : %s to %s' % (data[0],data[1]))
                    action(int(data[0]),int(data[1]))
            con.send('HTTP/1.1 200 OK\r\nContent-type: text/html\r\n\r\n')
            con.send(data[1])
            con.close()

def read_rf_scs():
    rx_pin = Pin(13, Pin.IN)
    max_length = 50
    dat = [0 for i in range(max_length)]
    level = 1
    i = 0
    n=1
    while n<9000 or n>11000:
        n = time_pulse_us(rx_pin, 0, 10000000)
    while i < max_length and n>0:
        n = time_pulse_us(rx_pin, level, 1000000)
        dat[i] = n
        i+=1
        level= 1-level
    out=''
    for n in range(0,48,2):
        if dat[n]>dat[n+1]:
            out+='1'
        else:
            out+='0'
    return out

def read_rf_smartwares():
    rx_pin = Pin(13, Pin.IN)
    max_length = 132
    dat = [0 for i in range(max_length)]
    level = 1
    i = 0
    n=1
    while n<9000 or n>11000:
        n = time_pulse_us(rx_pin, 0, 10000000)
    while i < max_length and n>0:
        n = time_pulse_us(rx_pin, level, 1000000)
        dat[i] = n
        i+=1
        level= 1-level
    out=''
    for n in range(2,130,4):
        if dat[n+1]>420:
            out+='0'
        else:
            out+='1'
    return out

devices={
    35:{'type': 'scs', 'code':['010101000100010101011100','010101000100010101010011']},
    37:{'type': 'scs', 'code':['010101000001010101011100','010101000001010101010011']},
    39:{'type': 'smartwares', 'code':['00000010110010110011010001110000','00000010110010110011010001100000']},
    40:{'type': 'smartwares', 'code':['00000010110010110011010001110001','00000010110010110011010001100001']},
    41:{'type': 'smartwares', 'code':['00000010110010110011010001110010','00000010110010110011010001100010']},
    42:{'type': 'smartwares', 'code':['00000010110010110011010001110011','00000010110010110011010001100011']},
    '39-42':{'type': 'smartwares', 'code':['00000010110010110011010001010000','00000010110010110011010001000000']},
    43:{'type': 'smartwares', 'code':['00000010001101111010110101110000','00000010001101111010110101100000']},
    44:{'type': 'smartwares', 'code':['00000010001101111010110101110001','00000010001101111010110101100001']},
    45:{'type': 'smartwares', 'code':['00000010001101111010110101110010','00000010001101111010110101100010']},
    46:{'type': 'smartwares', 'code':['00000010001101111010110101110011','00000010001101111010110101100011']},
    '43-46':{'type': 'smartwares', 'code':['00000010001101111010110101010000','00000010001101111010110101000000']}
    }

from time import sleep_us
def pulse(tx_pin, high_us, low_us):
    tx_pin(1)
    sleep_us(high_us) 
    tx_pin(0)
    sleep_us(low_us) 

def action(device_num, value):
    if devices[device_num]['type']=='smartwares':
        send_rf_smartwares(devices[device_num]['code'][value])
    elif devices[device_num]['type']=='scs':
        send_rf_scs(devices[device_num]['code'][value])
    send_to_server('%s,%s' % (device_num,value))
        
def send_rf_smartwares(data, pulselength=250, repeats=10):
    tx_pin = Pin(12, Pin.OUT)
    pulse(tx_pin,pulselength,pulselength*10) #start
    for n in range(repeats):
        for x in range(len(data)):
            if data[x]=='1':
                pulse(tx_pin,pulselength,pulselength)
                pulse(tx_pin,pulselength,pulselength*5) 
            else:
                pulse(tx_pin,pulselength,pulselength*5)
                pulse(tx_pin,pulselength,pulselength)
        pulse(tx_pin,pulselength,10000) #end
   
def send_rf_scs(data, pulselength=300, repeats=10):
    from time import sleep_us
    pulse3 = 3 * pulselength
    tx_pin = Pin(12, Pin.OUT)
    for n in range(repeats):
        for x in range(len(data)):
            if data[x]=='1':
                pulse(tx_pin,pulse3,pulselength)
            else:
                pulse(tx_pin,pulselength,pulse3)
        pulse(tx_pin,pulselength,10000) #end

start_wifi()
send_to_server('%s,%s' % (CAPTEUR_NUM, 0))
#serve()

RX_PIN = Pin(13, Pin.IN)

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
                #print(len(dat))
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
            temp2=temp2/17
            hum=eval('0b' + out[28:36])
            print (dat, out)
            print('%s °C %x %s' % (temp1+temp2, hum, '%H'))
        except:
            pass

