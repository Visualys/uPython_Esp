import network, ubinascii

mac = ubinascii.hexlify(network.WLAN().config('mac'),':').decode().upper()
print(mac)
