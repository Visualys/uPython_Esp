from machine import I2C, Pin
import time

class HTU21D(object):
    ADDRESS = 0x40
    ISSUE_TEMP_ADDRESS = 0xE3
    ISSUE_HU_ADDRESS = 0xE5

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

    def _issue_measurement(self, write_address):
        self.i2c.start()
        self.i2c.writeto_mem(int(self.ADDRESS), int(write_address), '')
        self.i2c.stop()
        time.sleep_ms(50)
        data = bytearray(3)
        self.i2c.readfrom_into(self.ADDRESS, data)
        if not self._crc_check(data):
            raise ValueError()
        raw = (data[0] << 8) + data[1]
        raw &= 0xFFFC
        return raw

    @property
    def temperature(self):
        """Calculate temperature"""
        raw = self._issue_measurement(self.ISSUE_TEMP_ADDRESS)
        return -46.85 + (175.72 * raw / 65536)

    @property
    def humidity(self):
        """Calculate humidity"""
        raw =  self._issue_measurement(self.ISSUE_HU_ADDRESS)
        return -6 + (125.0 * raw / 65536)


#sensor = HTU21D(22,21)
#hum = sensor.humidity
#temp = sensor.temperature
#print('Humidity : ', + hum)
#print('Temperature : ', + temp)
