import machine, time
D7 = machine.Pin(13)
speed=1/15

def ouvre():
    P = machine.PWM(D7, freq=50, duty = 0)
    for x in range(101):
        P.duty(100 - x + 20)
        time.sleep(speed)
        
def ferme():
    P = machine.PWM(D7, freq=50, duty = 0)
    for x in range(101):
        P.duty(x + 20)
        time.sleep(speed)
        print(x)
