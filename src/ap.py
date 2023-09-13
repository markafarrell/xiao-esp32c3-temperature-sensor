import machine
import network
import time

ssid="SensorNet"
password="SensorNet"

print("Creating WiFi AP")

ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=ssid, password=password)

print("Waiting for AP to be active")

while ap.active() == False:
    print('.', end='')
    time.sleep(0.1)
print()

print('AP created successfully. SSID: {ssid} Password: {password}')
print(ap.ifconfig())
