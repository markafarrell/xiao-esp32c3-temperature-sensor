#!/bin/bash

vlt login

touch secrets.py
truncate -s0 secrets.py

WIFI_SSID=$(vlt secrets get --plaintext WIFI_SSID)
WIFI_PASSWORD=$(vlt secrets get --plaintext WIFI_PASSWORD)

echo "wifi_ssid = \"$WIFI_SSID\"" >> secrets.py
echo "wifi_password = \"$WIFI_PASSWORD\"" >> secrets.py
