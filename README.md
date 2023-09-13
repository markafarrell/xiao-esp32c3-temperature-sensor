### Requirements

* [esptool](https://pypi.org/project/esptool/)
* [micropython]( https://micropython.org/download/esp32c3/)
* [mpremote](https://github.com/dhylands/rshell)


## Flash Firmware

1. Install esptool

```
pip install esptool
```

2. Get circuitpython

```
mkdir -p micropython
cd micropython
curl -O https://micropython.org/resources/firmware/ESP32_GENERIC_C3-20230426-v1.20.0.bin
```

3. Start ESP32C3 in bootloader mode (hold down boot button while powering up)

4. Identify serial device

```
sudo dmesg | grep "USB ACM device" | tail -1
```

```
[24659.642354] cdc_acm 1-1:1.0: ttyACM0: USB ACM device
```

5. Erase flash

```
esptool.py --chip esp32c3 --port /dev/ttyACM0 erase_flash
```

6. Flash circuit python firmware

```
esptool.py --chip esp32c3 --port /dev/ttyACM0 --baud 460800 write_flash -z 0x0 micropython/ESP32_GENERIC_C3-20230426-v1.20.0.bin
```

### Install

1. Install requirements

```
mpremote a0 mip install requests
mpremote a0 mip install microdot
```

2. Install application

```
mpremote a0 cp src/config.py :config.py
mpremote a0 cp src/config_web.py :config_web.py
mpremote a0 cp src/secrets.py :secrets.py
mpremote a0 cp src/sensor_mapping.py :sensor_mapping.py
mpremote a0 cp src/main.py :main.py
```

## Monitor Serial

### Connect

```
mpremote a0
```

