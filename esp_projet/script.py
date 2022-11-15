from machine import Pin, Timer
t1=Timer(-1)
t2=Timer(-1)
D1 = Pin(5, Pin.OUT)

def timer1():
    D1(1)
    t2.init(period=1000, mode=Timer.ONE_SHOT, callback=lambda t:timer2())

def timer2():
    D1(0)

def main():
    t1.init(period=5000, mode=Timer.PERIODIC, callback=lambda t:timer1())