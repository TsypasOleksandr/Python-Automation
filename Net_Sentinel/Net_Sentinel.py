[net_sentinel.py](https://github.com/user-attachments/files/28328625/net_sentinel.py)
import scapy.all as scapy
import socket
import argparse
import json
import os
import sys
from datetime import datetime

DB_FILE = "known_devices.json"

def get_local_ip_range():
    """Detects the local IP and calculates the /24 subnet."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        ip_parts = local_ip.split('.')
        ip_parts[3] = '0/24'
        return '.'.join(ip_parts)
    except Exception:
        print("[-] Could not dynamically determine IP. Defaulting to 192.168.1.0/24")
        return "192.168.1.0/24"

def scan_network(ip_range):
    """Performs an ARP broadcast scan to find active MAC addresses."""
    arp_request = scapy.ARP(pdst=ip_range)
    broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_packet = broadcast/arp_request
    
    # Send packet and capture responses
    answered_list = scapy.srp(arp_request_packet, timeout=2, verbose=False)[0]
    
    devices = []
    for element in answered_list:
        devices.append({"ip": element[1].psrc, "mac": element[1].hwsrc})
    return devices

def load_known_devices():
    """Loads the baseline database of trusted MAC addresses."""
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, 'r') as file:
        return json.load(file)

def save_known_devices(devices):
    """Saves the current devices as the trusted baseline."""
    with open(DB_FILE, 'w') as file:
        json.dump(devices, file, indent=4)
    print(f"[*] Baseline updated. Saved {len(devices)} devices to {DB_FILE}")

def main():
    parser = argparse.ArgumentParser(description="NetSentinel: Local Network Rogue Device Monitor")
    parser.add_argument("--baseline", action="store_true", help="Set current network state as the trusted baseline")
    parser.add_argument("--scan", action="store_true", help="Scan network and detect unknown/rogue devices")
    args = parser.parse_args()

    if not args.baseline and not args.scan:
        parser.print_help()
        sys.exit(1)

    print(f"[*] Initializing NetSentinel at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    ip_range = get_local_ip_range()
    print(f"[*] Target Subnet: {ip_range}")
    
    current_devices = scan_network(ip_range)
    
    if args.baseline:
        save_known_devices(current_devices)
        print("[+] Baseline establishment complete. Run with --scan to monitor.")
    
    elif args.scan:
        known_devices = load_known_devices()
        
        if not known_devices:
            print("[-] No baseline found! Please run 'sudo python3 net_sentinel.py --baseline' first.")
            sys.exit(1)
            
        known_macs = [device['mac'] for device in known_devices]
        
        print("\n" + "="*50)
        print("🛡️  NETWORK SECURITY SCAN REPORT  🛡️")
        print("="*50)
        
        rogue_found = False
        for device in current_devices:
            if device['mac'] not in known_macs:
                print(f"[!] ROGUE DEVICE DETECTED: IP: {device['ip']} | MAC: {device['mac']}")
                rogue_found = True
            else:
                print(f"[+] Trusted Device Found : IP: {device['ip']} | MAC: {device['mac']}")
                
        print("="*50)
        if not rogue_found:
            print("[*] Status: SECURE. No unauthorized devices detected.")
        else:
            print("[!] Status: WARNING. Unknown devices present on the network!")

if __name__ == "__main__":
    # Ensure script is run with administrative privileges
    if os.geteuid() != 0:
        print("[-] Error: Scapy requires administrative privileges.")
        print("[-] Please run the script with 'sudo'.")
        sys.exit(1)
    main()
