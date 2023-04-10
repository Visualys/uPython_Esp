from machine import UART

class pzem004tv3:
    def init(self, addr,rx, tx):
        self.addr=addr
        self.ser = UART(2, baudrate=9600, rx=rx, tx=tx, timeout=400)
        self.ser.init(9600, bits=8, parity=None, stop=1)
    def crc16(self, data):
        crc = 0xFFFF
        for c in data:
            crc = crc ^ c
            for j in range(8):
                if crc & 0x01:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc = crc >> 1
        return [crc & 0xFF, crc >> 8]
    def setaddress(self, addr):
        a=[0xf8, 0x06, 0x00, 0x02, 0, addr]
        a += self.crc16(a)
        self.ser.write(bytes(a))
        self.r = self.ser.read(8)
        if self.r!=None:
            if self.r[1]==0x06:
                self.addr=addr
                return 1
            else:
                return 0
        else:
            return 0
    def resetindex(self):
        a=[self.addr, 0x42]
        a += self.crc16(a)
        self.ser.write(bytes(a))
        self.r = self.ser.read(4)
        if self.r!=None:
            if self.r[1]==0x42:
                return 1
            else:
                return 0
        else:
            return 0   
    def read(self):
        a=[self.addr,0x04,0x00,0x00,0x00,0x0A]
        a += self.crc16(a)
        self.ser.write(bytes(a))
        self.r = self.ser.read(25)
        return self.r!=None
    def volts(self):
        return ((self.r[3] << 8) + self.r[4])/10
    def amps(self):
        return ((self.r[7] << 24) + (self.r[8] << 16) + (self.r[5] << 8) + self.r[6])/1000
    def watts(self):
        return ((self.r[11] << 24) + (self.r[12] << 16) + (self.r[9] << 8) + self.r[10])/10
    def index(self):
        return (self.r[15] << 24) + (self.r[16] << 16) + (self.r[13] << 8) + self.r[14]
    def freq(self):
        return ((self.r[17] << 8) + self.r[18])/10
    def fact(self):
        return ((self.r[19] << 8) + self.r[20])/100
    def alarm(self):
        return (self.r[21] << 8) + self.r[22]
