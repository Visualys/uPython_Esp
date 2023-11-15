from machine import I2C, Pin

class htu21d(object):
    def __init__(self, scl, sda):
        self.i2c = I2C(scl=Pin(scl), sda=Pin(sda), freq=100000)

    def _crc_check(self, value):
        remainder = ((value[0] << 8) + value[1]) << 8
        remainder |= value[2]
        divsor = 0x988000
        for i in range(0, 16):
            if remainder & 1 << (23 - i):
                remainder ^= divsor
            divsor >>= 1
        if remainder == 0:
            return True
        else:
            return False
        
    def _sendcommand(self, addr):
        self.i2c.start()
        self.i2c.writeto_mem(0x40, addr, '')
        self.i2c.stop()

    def _measure(self, addr):
        self._sendcommand(addr)
        data = bytearray(3)
        self.i2c.readfrom_into(0x40, data)
        if not self._crc_check(data):
            raise ValueError()
        raw = (data[0] << 8) + data[1]
        raw &= 0xFFFC
        return raw
    @property
    def temperature(self):
        raw = self._measure(0xE3)
        return round(0.002681274414 * raw - 46.85, 2)
    @property
    def humidity(self):
        raw =  self._measure(0xE5)
        return round(0.001907348633 * raw - 6, 2)
    @property
    def lowbattery(self):
        self._sendcommand(0xE7)
        data = bytearray(1)
        self.i2c.readfrom_into(0x40, data)
        return True if data[0] & 0x40 else False
