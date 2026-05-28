# Python-Automation

# NetSentinel Script Overview

In this lab summary, I reviewed the core functionality of the NetSentinel Python script, which acts as a basic Intrusion Detection System (IDS) for local networks.

## Description of Script Functionality

NetSentinel is an automated local network monitoring tool designed to detect unauthorized devices connected to a home or small office network.

The script performs several key tasks:

1. Scans the local subnet using ARP requests to discover active devices.
2. Creates a trusted baseline of known MAC addresses.
3. Monitors the network for unknown or rogue devices.
4. Alerts the user when unauthorized devices are detected.

The script uses Python together with the Scapy library to automate network discovery and monitoring tasks.

## Commands Used

### Create a trusted baseline
```bash
sudo python3 net_sentinel.py --baseline
```

### Scan the network for rogue devices
```bash
sudo python3 net_sentinel.py --scan
```

## Security Notes

- The script relies on the ARP protocol for device discovery.
- ARP scanning works only with IPv4 networks and does not detect IPv6 devices.
- Rogue device detection can potentially be bypassed using MAC spoofing techniques.
- This project is intended for educational and defensive cybersecurity practice.
