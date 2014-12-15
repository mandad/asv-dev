#!/bin/bash
sudo ip link set wlan0 up
wpa_supplicant -B -D nl80211 -i wlan0 -c /etc/wpa_supplicant.conf
sudo dhclient wlan0
ip route change default via 192.168.200.1 dev wlan0
