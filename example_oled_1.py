from machine import Pin, I2C
import sh1106
i2c = I2C(scl=Pin(5), sda=Pin(4), freq=400000)
display = sh1106.SH1106_I2C(128, 64, i2c, Pin(16), 0x3c)
display.sleep(False)
display.fill(0)
#
#display.text('Salut Aurelien', 0, 0, 1)
#display.text('ca marche aussi', 0, 22, 1)
#display.text('en micropython !', 0, 34, 1)
#display.line(4,28,4,30,1)
#display.fill_rect(0,15,128,2,2)
#display.line(10,50,20,50,1)
#display.line(20,50,60,60,1)
#display.line(60,60,120,45,1)
#display.line(60,45,120,70,1)
import math
for n in range(0,361):
    x=int(64+30*math.sin(n*3.14/180))
    y=int(32+30*math.cos(n*3.14/180))
    display.pixel(x,y,1)



display.show()
