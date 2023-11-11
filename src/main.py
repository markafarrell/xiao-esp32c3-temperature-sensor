import time
import machine
import onewire, ds18x20

import requests
import network

import secrets
import sensor_mapping

max_valid_temperature = 50
min_valid_temperature = -10

def pushMetric(pushgateway_url, job, name, value, type=None, labels=[]):
    '''
    cat <<EOF | curl --data-binary @- http://pushgateway.example.org:9091/metrics/job/some_job/instance/some_instance
    # TYPE some_metric counter
    some_metric{label="val1"} 42
    # TYPE another_metric gauge
    # HELP another_metric Just an example.
    another_metric 2398.283
    EOF
    '''
    data = ''

    if type is not None:
        data = data + f'# TYPE {name} {type}\n'

    label_data = ''
    first_label = True
    for label in labels:
        if not first_label:
            label_data = label_data + ','
        first_label = False
        label_data = label_data + f'{label["label"]}="{label["value"]}"'

    data = data + f'{name}{{{label_data}}} {value}\n'

    print(f'Pushing metric {data}')

    try:
        r = requests.post(
            f'{pushgateway_url}/metrics/job/{job}',data=data)
        r.close()
        del(r)
    except Exception as ex:
        print(f'Could not publish metric. {ex}')

sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)

if sta_if.isconnected():
    sta_if.disconnect()

print(f'Connecting to WiFi')
sta_if.connect(secrets.wifi_ssid, secrets.wifi_password)

while not sta_if.isconnected():
    print('.', end='')
    time.sleep(0.1)
print()

pushgateway_url = 'http://192.168.0.99:9091'

# Read battery voltage from GPIO2 A0
bat_pin = machine.Pin(2)

bat = machine.ADC(bat_pin, atten=machine.ADC.ATTN_11DB)

# We need to have a compensation factor for each board as the resistors
# in the voltage divider are not exactly the same value
# Multiplying the adc voldate by this factor will get us the actual
# battery voltage
voltage_divider_compensation_factor = 1.789
bat_voltage = bat.read_uv() / 1e6 * voltage_divider_compensation_factor

# the device is on GPIO9 D9
dat = machine.Pin(9)

# create the onewire object
ds = ds18x20.DS18X20(onewire.OneWire(dat))

# scan for devices on the bus
roms = ds.scan()

ds.convert_temp()
for rom in roms:
    rom_hex = ''.join('{:02x}'.format(x) for x in rom)
    print(f'found device: 0x{rom_hex}')

    temp = ds.read_temp(rom)
    if temp > max_valid_temperature or temp < min_valid_temperature:
        print(f'invalid temperature(0x{rom_hex})={temp}')
        time.sleep(0.1)
    else:
        print(f'temperature(0x{rom_hex})={temp}')

        labels = [
            {
                "label": "ROM",
                "value": f'0x{rom_hex}'
            }
        ]

        if f'0x{rom_hex}' in sensor_mapping.sensor_mapping:
            location = sensor_mapping.sensor_mapping[f'0x{rom_hex}']
            print(f'found sensor mapping 0x{rom_hex})={location}')
            labels.append(
                {
                    "label": "Location",
                    "value": location
                }
            )

        pushMetric(
            pushgateway_url=pushgateway_url,
            job='ds18x20-exporter',
            name='ds18x20_temperature_celsius',
            value=temp,
            type='gauge',
            labels=labels
        )

        pushMetric(
            pushgateway_url=pushgateway_url,
            job='ds18x20-exporter',
            name='ds18x20_battery_voltage',
            value=bat_voltage,
            type='gauge',
            labels=labels
        )

        time.sleep(0.1)

# put the device to sleep
machine.deepsleep(900000) # 15 Minutes
