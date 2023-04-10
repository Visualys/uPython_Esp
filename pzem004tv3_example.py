import time
from pzem004tv3 import pzem004tv3

pzem = pzem004tv3()
pzem.init(0x02, 18, 19)
#print(pzem.setaddress(0x02))
#print(pzem.resetindex())

time.sleep(2)
while True:
    if pzem.read():
        print('volts : %s' % pzem.volts())
        print('amps : %s' % pzem.amps())
        print('watts : %s' % pzem.watts())
        print('index : %s' % pzem.index())
        print('freq : %s' % pzem.freq())
        print('fact : %s' % pzem.fact())
        print('alarm : %s' % pzem.alarm())
    time.sleep(1)
