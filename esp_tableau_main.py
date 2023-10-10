import uasyncio
from microdot_asyncio import Microdot, send_file
import urequests
from machine import Timer, UART

dmxlevel = 0
dmx = UART(1)
dmx.init(250000, bits=8, parity=None, stop=2, invert=UART.INV_TX)
B = [0]
for n in range(8):
    B.append(0)

def write_frame():
    #print(dmxlevel)
    B[1]=int(round(dmxlevel,0))
    mes=bytes(B)
    dmx.sendbreak()
    dmx.write(mes)
    
t1 = Timer(0)
#t2 = Timer(1)
app = Microdot()

console = []

@app.route('/')
async def hello(request):
    return send_file('index.htm',200, {'Content-Type': 'text/html'})

@app.route('/js/<file>')
async def func(request, file):
    return send_file('js/{}'.format(file), max_age=3600)

@app.route('/start', methods=['GET', 'POST'])
async def start(request):
    t1.init(period=1000, mode=Timer.PERIODIC, callback=lambda t:mesure())
    return 'ok'

@app.route('/stop', methods=['GET', 'POST'])
async def stop(request):
    t1.deinit()
    return 'ok'

@app.route('/info', methods=['GET', 'POST'])
async def info(request):
    return '<br>'.join(console)

@app.route('/reboot', methods=['GET', 'POST'])
async def info(request):
    import machine
    machine.reset()
    return 'ok'

async def start_server():
    print('startint microdot app')
    try:
        await app.run(port=80, debug=True)
    except:
        await app.shutdown()

import time
from pzem004tv3 import pzem004tv3

pzem1 = pzem004tv3()
pzem1.init(0x01, 19, 18)
pzem2 = pzem004tv3()
pzem2.init(0x02, 19, 18)
pzem3 = pzem004tv3()
pzem3.init(0x03, 19, 18)

#print(pzem.setaddress(0x02))
#print(pzem.resetindex())

loopcod=0

def mesure():
    global console, loopcod, dmxlevel
    loopcod+=1
    dic=[]
    write_frame() # SEND DMX
    if pzem1.read():
        p=pzem1.watts()
        dic.append('10')
        dic.append(str(p))
        v=pzem1.volts()
        dic.append('11')
        dic.append(str(v))    
        f=pzem1.freq()
        dic.append('12')
        dic.append(str(f))
        c=pzem1.index()
        dic.append('13')
        dic.append(str(c))
        console.append('volts : {}'.format(pzem1.volts()))
        console = console[-14:]
    if pzem2.read():
        p2=pzem2.watts()
        dic.append('18')
        dic.append(str(p2))
        c2=pzem2.index()
        dic.append('19')
        dic.append(str(c2))
    if pzem3.read():
        p3=pzem3.watts()
        dic.append('20')
        dic.append(str(p3))
        c3=pzem3.index()
        dic.append('21')
        dic.append(str(c3))
    dic.append('22')
    dic.append(str(int(round(dmxlevel,0))))
    write_frame() # SEND DMX
    if loopcod==5:
        loopcod=0
        if len(dic)>0:
            r = urequests.get('http://192.168.1.32:8080/dmx?mes={}'.format(','.join(dic)))
    diff = p-p2
    dmxlevel-=(diff/25)
    if dmxlevel<0:
        dmxlevel=0
    if dmxlevel>255:
        dmxlevel=255
    write_frame() # SEND DMX
   
t1.init(period=800, mode=Timer.PERIODIC, callback=lambda t:mesure())
#t2.init(period=600, mode=Timer.PERIODIC, callback=lambda t:write_frame())

uasyncio.run(start_server())

 