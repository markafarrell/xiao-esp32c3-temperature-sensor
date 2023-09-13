import time
import machine
import onewire, ds18x20

import requests
import network

import secrets
import sensor_mapping
import config

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

def createAP(ssid, password):
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=ssid, password=password)

    print("Waiting for AP to be active")
    while ap.active() == False:
        print('.', end='')
        time.sleep(0.1)
        pass

    print('AP created successfully. SSID: {ssid} Password: {password}')
    print(ap.ifconfig())

    return ap

def connectWifi(
        ssid,
        password,
        wifi_connect_timeout_seconds=10,
        wifi_connect_timeout_interval=0.1
    ):
    '''
        Attempt to connect to wifi.
    '''
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)

    if sta_if.isconnected():
        sta_if.disconnect()

    print(f'Connecting to WiFi SSID:{ssid} Password:{password}')
    sta_if.connect(ssid, password)

    wifi_connect_timeout_seconds = 10  # Seconds
    wifi_connect_timeout_interval = 0.1  # Seconds

    for i in range(wifi_connect_timeout_seconds *  wifi_connect_timeout_interval):
        if sta_if.isconnected():
            break
        print('.', end='')
        time.sleep(wifi_connect_timeout_interval)
    print()

    return sta_if

# 1. Attempt to connect to WIFI using secrets

sta_if = connectWifi(secrets.wifi_ssid, secrets.wifi_password)

if not sta_if.isconnected():
    # If we can't connect to wifi with stored credentials after
    # wifi_connect_timeout_seconds then start Broadcast an AP and
    # start a web server to allow credentials to be entered

    # Deactivate STA
    sta_if.active(False)

    ap = createAP("SensorNet", "SensorNet")

    # import config_web
    # config_web.app.run(debug=True)

    time.sleep(1000)

    # After the webserver is terminated we reset so that we can use the new
    # settings to connect
    machine.reset()

else:
    connection_details = sta_if.ifconfig()
    # this returns a 4-tuple
    # (ip, subnet, gateway, dns)
    print(f'Connected to {secrets.wifi_ssid}. IP: {connection_details[0]} subnet: {connection_details[1]} gateway: {connection_details[2]} dns: {connection_details[3]}')

# the device is on GPIO7 D5
dat = machine.Pin(7)

# create the onewire object
ds = ds18x20.DS18X20(onewire.OneWire(dat))

# scan for devices on the bus
roms = ds.scan()
print('found devices:', roms)

ds.convert_temp()
for rom in roms:
    rom_hex = ''.join('{:02x}'.format(x) for x in rom)

    temp = ds.read_temp(rom)
    if temp > max_valid_temperature or temp < min_valid_temperature:
        print(f'invalid temperature(0x{rom_hex})={temp}')
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
            pushgateway_url=config.pushgateway_url,
            job='ds18x20-exporter',
            name='ds18x20_temperature_celsius',
            value=temp,
            type='gauge',
            labels=labels
        )

# put the device to sleep
# machine.deepsleep(30000)
