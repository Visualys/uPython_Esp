from machine import Pin, Timer
from time import sleep
import network, ubinascii, uos
import usocket as socket, uselect as select
import urequests
import json
import os
import sys
from script import *
D1 = Pin(5, Pin.OUT)
D7 = Pin(13, Pin.OUT)
if 'main' in dir():
    main()

ret=''

def urldecode(s):
    x=s.find('%')
    while x>-1:
        c=chr(int('0x'+s[x+1:x+3]))
        s = s[:x]+c+s[x+3:]
        x=s.find('%')
    s=s.replace('+',' ')
    return s

def setvar(s):
    global dic
    n1=s.find('%%')
    while n1>-1:
        n1+=2
        n2 = n1 + s[n1:].find('%%')
        try:
            v = eval(s[n1:n2])
        except:
            v = ''
            pass
        s = s[:n1-2]+str(v)+s[n2+2:]
        n1=s.find('%%')
    return s

def parsefields(query):
    d={}
    if len(query)>1:
        for x in query[1].split('&'):
            t=x.split('=')
            if len(t)>1:
                d[t[0]]=urldecode(t[1])
            else:
                d[t[0]]=''
    return d

def givefile(filename):
    f=open(filename,'r')
    s=f.read()
    f.close
    if filename=='prompt_out.htm':
        dic2 = parsefields(query)
        if 'lng' in dic2:
            exec(dic2['lng'])
    if filename=='script_out.htm':
        dic2 = parsefields(query)
        if 'scr' in dic2:
            f=open('script.py','w')
            f.write(dic2['scr'])
            f.close()
            import machine
            machine.reset()

    if filename.endswith('.htm'):
        return setvar(s)
    else:
        return s

f=open('dic.dat','r')
dic = eval(f.read())
f.close()
scr=''

ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=dic['apnam'], password=dic['appw'], hidden=int(dic['aphi']))

led = Pin(2, Pin.OUT)
led(0)

sta = network.WLAN(network.STA_IF)
sta.active(True)
if dic['hn']:
    sta.config(dhcp_hostname=dic['hn'])

sta.connect(dic['ssid'], dic['wpwd'])

for n in range(10):
    if sta.isconnected():
        break
    sleep(1)
    print('.', end='')

if sta.isconnected():
    print('')
    print('wifi connecté (', sta.ifconfig()[0],')')
    print('hostname',sta.config('dhcp_hostname'))
    if dic['apoff']=='1':ap.active(False)

led(1)
a=0

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)
dic2={}
while True:
    if(sta.isconnected()==False):
        led = Pin(2, Pin.OUT)
        led(0)
        #wifi_connect()
        led(1)
        
    gc.collect()
    conn, addr = s.accept()
    print('Connection from %s' % str(addr))
    response=''
    led(0)
    request=''
    buffer = conn.recv(1024)
    request += buffer.decode('utf-8')
    while len(buffer)==1024:
        buffer = conn.recv(1024)
        request += buffer.decode('utf-8')
    if len(request)==0:
        print("zero length request.")
        conn.close()
        continue
    query = request.split('\r\n')[0].split(' ')[1].split('?')
    if len(query)>1:
        #print(urldecode(query[1]))
        print('length:',len(query[1]))
    if query[0]=="/": query[0]="/index.htm"
    if query[0][1:] in os.listdir('/'):
        conn.send('HTTP/1.1 200 OK\n')
        if query[0][1:]=='styles.css':
            conn.send('Content-Type: text/css; charset=utf-8\n')
            conn.send('Cache-Control: max-age=60\n')
        else:
            conn.send('Content-Type: text/html; charset=utf-8\n')
        conn.send('Connection: close\n\n')
        response=givefile(query[0][1:])
        print('transfer:',query[0][1:])
        conn.sendall(response)
    elif len(query[0])>0:
        dic2 = parsefields(query)
        if query[0]=="/run":
            if 'code' in dic2:
                exec(dic2['code'])
                response = 'code executé.'
        elif query[0]=='/Save':
            if not 'apoff' in dic2:dic2['apoff']='0'
            if not 'aphi' in dic2:dic2['aphi']='0'
            dic.update(dic2)
            f=open('dic.dat','w')
            f.write(json.dumps(dic))
            f.close()
            response = 'OK'
        print(response)
        conn.send('HTTP/1.1 200 OK\n')
        conn.send('Content-Type: text/html; charset=utf-8\n')
        conn.send('Connection: close\n\n')
        conn.sendall(response)
    conn.close()
    led(1)
