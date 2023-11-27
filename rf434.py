from machine import Pin, time_pulse_us
from time import ticks_us

rx_pin = Pin(13, Pin.IN)

def read_rf():
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
    return dat, out
    
#read_rf(rx_pin)

    
def rfcommand_prise2(val, pulselength=280, repeats=8):
    from time import sleep_us
    pulse3 = 3 * pulselength
    tx_pin = Pin(12, Pin.OUT)
    if val:
        data='010101000100010101010011'
    else:
        data='010101000100010101011100'
    for n in range(repeats):
        for x in range(len(data)):
            tx_pin(1)
            if data[x]=='1':
                sleep_us(pulse3)  
            else:
                sleep_us(pulselength)
            tx_pin(0)
            if data[x]=='1':
                sleep_us(pulselength)  
            else:
                sleep_us(pulse3)
        tx_pin(1)
        sleep_us(pulselength) 
        tx_pin(0)
        sleep_us(pulselength*10) 

