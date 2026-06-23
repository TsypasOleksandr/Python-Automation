"""
MacSpoofer Pro v4.0 - Продвинутый инструмент для управления MAC-адресами
Поддерживает: macOS, Linux, Windows
Автор: OlTs
"""

import subprocess
import re
import os
import sys
import time
import random
import json
import socket
import platform
from datetime import datetime
import argparse
from ipaddress import ip_network, ip_address

# Попытка импорта дополнительных библиотек
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

# ==================== ОПРЕДЕЛЕНИЕ ОС ====================
OS_TYPE = platform.system().lower()
IS_MAC = OS_TYPE == "darwin"
IS_LINUX = OS_TYPE == "linux"
IS_WINDOWS = OS_TYPE == "windows"

# ==================== ЦВЕТА ДЛЯ ВЫВОДА ====================
class Colors:
    """Класс для цветного вывода в терминал"""
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

def print_colored(text, color=Colors.WHITE):
    """Вывод цветного текста"""
    if IS_WINDOWS:
        print(text)
    else:
        print(f"{color}{text}{Colors.RESET}")

# ==================== ПРОВЕРКА НАЛИЧИЯ КОМАНД ====================

def check_command_exists(command):
    """Проверка существования команды в системе"""
    try:
        subprocess.check_output(["which", command], stderr=subprocess.DEVNULL)
        return True
    except:
        try:
            subprocess.check_output(["where", command], stderr=subprocess.DEVNULL, shell=True)
            return True
        except:
            return False

def get_available_commands():
    """Получение доступных команд для работы с сетью"""
    commands = {
        "ip": check_command_exists("ip") if not IS_WINDOWS else False,
        "ifconfig": check_command_exists("ifconfig"),
        "arp": check_command_exists("arp"),
        "arp-scan": check_command_exists("arp-scan"),
        "nmap": check_command_exists("nmap"),
        "iwgetid": check_command_exists("iwgetid"),
        "nmcli": check_command_exists("nmcli"),
        "ping": check_command_exists("ping"),
        "hostname": check_command_exists("hostname"),
        "netsh": check_command_exists("netsh") if IS_WINDOWS else False,
        "wmic": check_command_exists("wmic") if IS_WINDOWS else False,
        "networksetup": check_command_exists("networksetup") if IS_MAC else False,
    }
    return commands

# ==================== ПОЛУЧЕНИЕ ИНТЕРФЕЙСОВ ====================

def get_network_interfaces():
    """Получение списка сетевых интерфейсов"""
    interfaces = []
    
    if IS_MAC:
        # macOS
        try:
            # Получаем список интерфейсов
            result = subprocess.check_output(["ifconfig", "-l"]).decode().strip()
            all_interfaces = result.split()
            
            for intf in all_interfaces:
                if intf.startswith('en') or intf.startswith('eth'):
                    try:
                        output = subprocess.check_output(["ifconfig", intf]).decode()
                        if "ether" in output:
                            interfaces.append(intf)
                    except:
                        pass
            
            interfaces = list(set(interfaces))
            
        except Exception as e:
            print_colored(f"Ошибка получения интерфейсов: {e}", Colors.RED)
    
    elif IS_LINUX:
        # Linux
        if check_command_exists("ip"):
            try:
                result = subprocess.check_output(["ip", "link", "show"]).decode("utf-8")
                for line in result.split("\n"):
                    match = re.search(r'^\d+:\s+([a-zA-Z0-9_]+):', line)
                    if match:
                        interface = match.group(1)
                        if interface not in ['lo', 'docker', 'veth', 'br-'] and not interface.startswith('veth'):
                            interfaces.append(interface)
            except:
                pass
        
        if not interfaces and check_command_exists("ifconfig"):
            try:
                result = subprocess.check_output(["ifconfig"]).decode("utf-8")
                for line in result.split("\n"):
                    match = re.search(r'^([a-zA-Z0-9_]+):', line)
                    if match:
                        interface = match.group(1)
                        if interface not in ['lo', 'docker0']:
                            interfaces.append(interface)
            except:
                pass
    
    elif IS_WINDOWS:
        # Windows
        try:
            result = subprocess.check_output(["netsh", "interface", "show", "interface"], shell=True).decode()
            for line in result.split("\n"):
                parts = line.split()
                if len(parts) >= 4 and "connected" in line.lower():
                    interface = " ".join(parts[3:])
                    interfaces.append(interface)
        except:
            pass
    
    return interfaces

def get_current_mac(interface):
    """Получение текущего MAC-адреса интерфейса"""
    
    if IS_MAC:
        try:
            result = subprocess.check_output(["ifconfig", interface]).decode()
            match = re.search(r'ether\s+([0-9a-fA-F:]{17})', result)
            if match:
                return match.group(1)
        except:
            pass
    
    elif IS_LINUX:
        if check_command_exists("ip"):
            try:
                result = subprocess.check_output(["ip", "link", "show", interface]).decode()
                match = re.search(r'link/ether\s+([0-9a-fA-F:]{17})', result)
                if match:
                    return match.group(1)
            except:
                pass
        
        if check_command_exists("ifconfig"):
            try:
                result = subprocess.check_output(["ifconfig", interface]).decode()
                for line in result.split("\n"):
                    if "ether" in line or "HWaddr" in line:
                        match = re.search(r'(?:ether|HWaddr)\s+([0-9a-fA-F:]{17})', line)
                        if match:
                            return match.group(1)
            except:
                pass
    
    elif IS_WINDOWS:
        try:
            result = subprocess.check_output(["wmic", "nic", "where", "NetEnabled=true", "get", "MACAddress,Name"], shell=True).decode()
            for line in result.split("\n"):
                if interface in line:
                    parts = line.split()
                    for part in parts:
                        if re.match(r'^[0-9a-fA-F]{2}-[0-9a-fA-F]{2}-[0-9a-fA-F]{2}-[0-9a-fA-F]{2}-[0-9a-fA-F]{2}-[0-9a-fA-F]{2}$', part):
                            return part.replace('-', ':')
        except:
            pass
    
    return "00:00:00:00:00:00"

def get_ip_address(interface):
    """Получение IP-адреса интерфейса"""
    if IS_MAC or IS_LINUX:
        if check_command_exists("ip"):
            try:
                result = subprocess.check_output(["ip", "addr", "show", interface]).decode()
                match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)/\d+', result)
                if match:
                    return match.group(1)
            except:
                pass
        
        if check_command_exists("ifconfig"):
            try:
                result = subprocess.check_output(["ifconfig", interface]).decode()
                match = re.search(r'inet\s+(?:addr:)?(\d+\.\d+\.\d+\.\d+)', result)
                if match:
                    return match.group(1)
            except:
                pass
    
    elif IS_WINDOWS:
        try:
            result = subprocess.check_output(["ipconfig"], shell=True).decode()
            lines = result.split("\n")
            found = False
            for line in lines:
                if interface in line:
                    found = True
                if found and "IPv4" in line:
                    match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                    if match:
                        return match.group(1)
        except:
            pass
    
    return None

# ==================== СМЕНА MAC-АДРЕСА ====================

def set_new_mac(interface, new_mac, verbose=True):
    """Изменение MAC-адреса интерфейса (поддержка всех ОС)"""
    if verbose:
        print_colored(f"Изменение MAC-адреса интерфейса {interface} на {new_mac}", Colors.YELLOW)
    
    try:
        # Проверяем существование интерфейса
        interfaces = get_network_interfaces()
        if interface not in interfaces:
            print_colored(f"Интерфейс {interface} не найден", Colors.RED)
            return False
        
        if IS_MAC:
            # === macOS ===
            return set_mac_macos(interface, new_mac, verbose)
        
        elif IS_LINUX:
            # === Linux ===
            return set_mac_linux(interface, new_mac, verbose)
        
        elif IS_WINDOWS:
            # === Windows ===
            return set_mac_windows(interface, new_mac, verbose)
        
        else:
            print_colored(f"Неподдерживаемая ОС: {OS_TYPE}", Colors.RED)
            return False
            
    except Exception as e:
        if verbose:
            print_colored(f"✗ Ошибка: {e}", Colors.RED)
        return False

def set_mac_macos(interface, new_mac, verbose=True):
    """Смена MAC на macOS"""
    try:
        # Отключаем интерфейс
        subprocess.run(["sudo", "ifconfig", interface, "down"], 
                      stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, check=False)
        time.sleep(1)
        
        # Пробуем ether
        result = subprocess.run(["sudo", "ifconfig", interface, "ether", new_mac],
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            # Пробуем lladdr
            result = subprocess.run(["sudo", "ifconfig", interface, "lladdr", new_mac],
                                  capture_output=True, text=True)
        
        time.sleep(1)
        
        # Включаем интерфейс
        subprocess.run(["sudo", "ifconfig", interface, "up"], 
                      stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, check=False)
        time.sleep(1)
        
        # Проверяем результат
        new_mac_after = get_current_mac(interface)
        
        if new_mac_after.lower() == new_mac.lower():
            if verbose:
                print_colored("✓ MAC-адрес успешно изменён!", Colors.GREEN)
            return True
        else:
            if verbose:
                print_colored(f"✗ MAC не изменился. Текущий: {new_mac_after}", Colors.RED)
            return False
            
    except Exception as e:
        if verbose:
            print_colored(f"✗ Ошибка: {e}", Colors.RED)
        return False

def set_mac_linux(interface, new_mac, verbose=True):
    """Смена MAC на Linux"""
    try:
        if check_command_exists("ip"):
            # Отключаем интерфейс
            subprocess.run(["sudo", "ip", "link", "set", interface, "down"], 
                          stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, check=False)
            time.sleep(0.5)
            
            # Меняем MAC
            subprocess.run(["sudo", "ip", "link", "set", interface, "address", new_mac],
                          stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, check=True)
            time.sleep(0.5)
            
            # Включаем интерфейс
            subprocess.run(["sudo", "ip", "link", "set", interface, "up"],
                          stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, check=False)
            
        elif check_command_exists("ifconfig"):
            # Отключаем интерфейс
            subprocess.run(["sudo", "ifconfig", interface, "down"], 
                          stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, check=False)
            time.sleep(0.5)
            
            # Меняем MAC
            subprocess.run(["sudo", "ifconfig", interface, "ether", new_mac],
                          stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, check=True)
            time.sleep(0.5)
            
            # Включаем интерфейс
            subprocess.run(["sudo", "ifconfig", interface, "up"],
                          stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, check=False)
        else:
            print_colored("Не найдено ни ip, ни ifconfig", Colors.RED)
            return False
        
        time.sleep(1)
        
        # Проверяем результат
        new_mac_after = get_current_mac(interface)
        
        if new_mac_after.lower() == new_mac.lower():
            if verbose:
                print_colored("✓ MAC-адрес успешно изменён!", Colors.GREEN)
            return True
        else:
            if verbose:
                print_colored(f"✗ MAC не изменился. Текущий: {new_mac_after}", Colors.RED)
            return False
            
    except Exception as e:
        if verbose:
            print_colored(f"✗ Ошибка: {e}", Colors.RED)
        return False

def set_mac_windows(interface, new_mac, verbose=True):
    """Смена MAC на Windows"""
    try:
        # Получаем имя адаптера
        result = subprocess.check_output(["netsh", "interface", "show", "interface"], shell=True).decode()
        adapter_name = None
        
        for line in result.split("\n"):
            if interface in line:
                parts = line.split()
                if len(parts) >= 4:
                    adapter_name = " ".join(parts[3:])
                    break
        
        if not adapter_name:
            print_colored(f"Адаптер {interface} не найден", Colors.RED)
            return False
        
        # Отключаем адаптер
        subprocess.run(["netsh", "interface", "set", "interface", adapter_name, "admin=disable"], 
                      shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, check=False)
        time.sleep(2)
        
        # Меняем MAC через реестр (требует прав администратора)
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}")
            # Ищем подходящий ключ с MAC
            for i in range(100):
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkey = winreg.OpenKey(key, subkey_name)
                    try:
                        desc, _ = winreg.QueryValueEx(subkey, "DriverDesc")
                        if interface in desc or adapter_name in desc:
                            winreg.SetValueEx(subkey, "NetworkAddress", 0, winreg.REG_SZ, new_mac.replace(':', ''))
                            break
                    except:
                        pass
                    winreg.CloseKey(subkey)
                except:
                    break
            winreg.CloseKey(key)
        except:
            # Альтернативный метод через PowerShell
            subprocess.run(["powershell", f"-Command", 
                          f"Get-NetAdapter -Name '{interface}' | Set-NetAdapter -MacAddress '{new_mac}'"], 
                          shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, check=False)
        
        time.sleep(2)
        
        # Включаем адаптер
        subprocess.run(["netsh", "interface", "set", "interface", adapter_name, "admin=enable"], 
                      shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, check=False)
        time.sleep(2)
        
        if verbose:
            print_colored("✓ MAC-адрес изменён! (требуется перезагрузка для применения)", Colors.GREEN)
        return True
        
    except Exception as e:
        if verbose:
            print_colored(f"✗ Ошибка: {e}", Colors.RED)
        return False

# ==================== ФУНКЦИЯ СКАНИРОВАНИЯ СЕТИ ====================

def scan_network(interface=None):
    """Сканирование сети и получение списка подключенных устройств"""
    devices = []
    available_commands = get_available_commands()
    
    try:
        # Получаем IP и сеть интерфейса
        if interface:
            network = get_network_range(interface)
        else:
            interfaces = get_network_interfaces()
            for intf in interfaces:
                network = get_network_range(intf)
                if network:
                    interface = intf
                    break
            else:
                print_colored("Не найден активный сетевой интерфейс", Colors.RED)
                return []
        
        if not network:
            print_colored("Не удалось определить сеть", Colors.RED)
            return []
        
        print_colored(f"Сканирование сети: {network}", Colors.CYAN)
        
        # Метод 1: arp-scan (Linux/macOS)
        if available_commands.get("arp-scan", False):
            try:
                result = subprocess.check_output(["arp-scan", "--localnet"], 
                                               stderr=subprocess.DEVNULL).decode()
                
                for line in result.split("\n"):
                    parts = line.split("\t")
                    if len(parts) >= 2 and re.match(r'\d+\.\d+\.\d+\.\d+', parts[0]):
                        ip = parts[0].strip()
                        mac = parts[1].strip() if len(parts) > 1 else "Unknown"
                        vendor = parts[2].strip() if len(parts) > 2 else "Unknown"
                        
                        try:
                            hostname = socket.gethostbyaddr(ip)[0]
                        except:
                            hostname = "Unknown"
                        
                        devices.append({
                            "ip": ip,
                            "mac": mac,
                            "vendor": vendor,
                            "hostname": hostname,
                            "status": "active"
                        })
                
                if devices:
                    return devices
                    
            except:
                pass
        
        # Метод 2: nmap
        if available_commands.get("nmap", False):
            try:
                result = subprocess.check_output(["nmap", "-sn", network], 
                                               stderr=subprocess.DEVNULL).decode()
                
                ips = re.findall(r'Nmap scan report for (?:.*?)\s*\(?(\d+\.\d+\.\d+\.\d+)\)?', result)
                macs = re.findall(r'MAC Address: ([0-9A-F:]{17})', result)
                
                for i, ip in enumerate(ips):
                    mac = macs[i] if i < len(macs) else "Unknown"
                    try:
                        hostname = socket.gethostbyaddr(ip)[0]
                    except:
                        hostname = "Unknown"
                    
                    devices.append({
                        "ip": ip,
                        "mac": mac,
                        "vendor": get_vendor_by_mac(mac) if mac != "Unknown" else "Unknown",
                        "hostname": hostname,
                        "status": "active"
                    })
                
                if devices:
                    return devices
                    
            except:
                pass
        
        # Метод 3: ARP таблица
        if available_commands.get("arp", False):
            try:
                result = subprocess.check_output(["arp", "-a"]).decode()
                
                for line in result.split("\n"):
                    if IS_WINDOWS:
                        match = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+([0-9a-f-]+)', line, re.IGNORECASE)
                        if match:
                            ip = match.group(1)
                            mac = match.group(2).replace('-', ':').upper()
                    else:
                        match = re.search(r'\((\d+\.\d+\.\d+\.\d+)\)\s+at\s+([0-9a-f:]+)', line, re.IGNORECASE)
                        if match:
                            ip = match.group(1)
                            mac = match.group(2).upper()
                        else:
                            continue
                    
                    try:
                        hostname = socket.gethostbyaddr(ip)[0]
                    except:
                        hostname = "Unknown"
                    
                    devices.append({
                        "ip": ip,
                        "mac": mac,
                        "vendor": get_vendor_by_mac(mac) if mac != "Unknown" else "Unknown",
                        "hostname": hostname,
                        "status": "active"
                    })
                
                if devices:
                    return devices
                    
            except:
                pass
        
        # Метод 4: Ping sweep (медленный, но без доп. утилит)
        if available_commands.get("ping", False):
            try:
                if "/" in network:
                    try:
                        network_obj = ip_network(network, strict=False)
                        hosts = list(network_obj.hosts())
                        hosts_to_scan = hosts[:254]
                    except:
                        ip_parts = network.split('/')[0].split('.')
                        if len(ip_parts) == 4:
                            base = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}"
                            hosts_to_scan = [f"{base}.{i}" for i in range(1, 255)]
                        else:
                            hosts_to_scan = []
                else:
                    ip_parts = network.split('.')
                    if len(ip_parts) == 4:
                        base = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}"
                        hosts_to_scan = [f"{base}.{i}" for i in range(1, 255)]
                    else:
                        hosts_to_scan = []
                
                print_colored(f"Сканирование {len(hosts_to_scan)} адресов...", Colors.YELLOW)
                
                for ip_str in hosts_to_scan[:100]:
                    try:
                        if IS_WINDOWS:
                            subprocess.check_output(["ping", "-n", "1", "-w", "1000", ip_str],
                                                  stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                        else:
                            subprocess.check_output(["ping", "-c", "1", "-W", "1", ip_str],
                                                  stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                        
                        if available_commands.get("arp", False):
                            try:
                                if IS_WINDOWS:
                                    arp_result = subprocess.check_output(["arp", "-a", ip_str], shell=True).decode()
                                else:
                                    arp_result = subprocess.check_output(["arp", "-a", ip_str]).decode()
                                
                                if IS_WINDOWS:
                                    mac_match = re.search(r'([0-9a-f]{2}-[0-9a-f]{2}-[0-9a-f]{2}-[0-9a-f]{2}-[0-9a-f]{2}-[0-9a-f]{2})', arp_result, re.IGNORECASE)
                                    mac = mac_match.group(1).replace('-', ':').upper() if mac_match else "Unknown"
                                else:
                                    mac_match = re.search(r'at\s+([0-9a-f:]+)', arp_result, re.IGNORECASE)
                                    mac = mac_match.group(1).upper() if mac_match else "Unknown"
                            except:
                                mac = "Unknown"
                        else:
                            mac = "Unknown"
                        
                        try:
                            hostname = socket.gethostbyaddr(ip_str)[0]
                        except:
                            hostname = "Unknown"
                        
                        devices.append({
                            "ip": ip_str,
                            "mac": mac,
                            "vendor": get_vendor_by_mac(mac) if mac != "Unknown" else "Unknown",
                            "hostname": hostname,
                            "status": "active"
                        })
                        
                        print_colored(f"Найдено устройство: {ip_str} ({mac})", Colors.GREEN)
                        
                    except:
                        pass
                
            except:
                pass
    
    except Exception as e:
        print_colored(f"Ошибка сканирования: {e}", Colors.RED)
    
    return devices

def get_network_range(interface):
    """Получение сети интерфейса с маской"""
    ip = get_ip_address(interface)
    if ip:
        parts = ip.split('.')
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
    return None

def get_vendor_by_mac(mac):
    """Определение производителя по MAC-адресу"""
    oui_db = {
        "00:1A:2B": "Apple Inc.",
        "00:1C:B3": "Apple Inc.",
        "00:1E:52": "Apple Inc.",
        "00:15:5D": "Intel Corporation",
        "00:1B:21": "Intel Corporation",
        "00:1E:37": "Intel Corporation",
        "00:16:6B": "Samsung Electronics",
        "00:1E:DF": "Samsung Electronics",
        "00:14:22": "Dell Inc.",
        "00:1D:09": "Dell Inc.",
        "00:1B:54": "Cisco Systems",
        "00:1D:45": "Cisco Systems",
        "00:1A:4B": "Hewlett Packard",
        "00:1B:78": "Hewlett Packard",
        "00:1A:92": "ASUSTek Computer",
        "00:1E:8C": "ASUSTek Computer",
        "00:1C:25": "Lenovo",
        "00:1D:72": "Lenovo",
        "00:1A:80": "Acer Inc.",
        "00:1B:D0": "Acer Inc.",
        "00:1D:36": "Toshiba",
        "00:1E:33": "Toshiba",
        "08:00:27": "VirtualBox",
        "00:0C:29": "VMware",
        "00:50:56": "VMware",
        "00:23:7D": "Microsoft Corporation",
    }
    
    if mac and len(mac) >= 8:
        oui = mac[:8].upper()
        return oui_db.get(oui, "Unknown")
    return "Unknown"

def display_network_devices(devices):
    """Отображение найденных устройств"""
    if not devices:
        print_colored("Устройства не найдены", Colors.YELLOW)
        return
    
    print_colored("\n" + "="*100, Colors.BOLD)
    print_colored("   НАЙДЕННЫЕ УСТРОЙСТВА В СЕТИ", Colors.BLUE)
    print_colored("="*100, Colors.BOLD)
    print(f"{'IP-адрес':<20} {'MAC-адрес':<20} {'Производитель':<25} {'Имя хоста':<20} {'Статус':<10}")
    print("-"*100)
    
    for device in devices:
        ip = device.get('ip', 'Unknown')
        mac = device.get('mac', 'Unknown')
        vendor = device.get('vendor', 'Unknown')[:25]
        hostname = device.get('hostname', 'Unknown')[:20]
        
        print_colored(
            f"{ip:<20} {mac:<20} {vendor:<25} {hostname:<20} active",
            Colors.GREEN
        )
    
    print("-"*100)
    print_colored(f"Всего найдено устройств: {len(devices)}", Colors.BOLD)
    print_colored("="*100 + "\n", Colors.BOLD)

def save_scan_results(devices, filename=None):
    """Сохранение результатов сканирования"""
    if not filename:
        filename = f"network_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        os.makedirs(os.path.expanduser("~/.mac_spoofer_scans"), exist_ok=True)
        filepath = os.path.join(os.path.expanduser("~/.mac_spoofer_scans"), filename)
        
        with open(filepath, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "os": OS_TYPE,
                "devices": devices
            }, f, indent=2)
        
        print_colored(f"✓ Результаты сохранены в: {filepath}", Colors.GREEN)
        return filepath
    except Exception as e:
        print_colored(f"✗ Ошибка сохранения: {e}", Colors.RED)
        return None

# ==================== ГЕНЕРАЦИЯ MAC ====================

def generate_mac_by_vendor(vendor_name):
    """Генерация MAC-адреса с привязкой к производителю"""
    vendors = {
        "apple": ["00:1A:2B", "00:1C:B3", "00:1E:52"],
        "intel": ["00:15:5D", "00:1B:21", "00:1E:37"],
        "samsung": ["00:16:6B", "00:1E:DF", "00:1F:DF"],
        "dell": ["00:14:22", "00:1D:09", "00:1E:C9"],
        "cisco": ["00:1B:54", "00:1D:45", "00:1E:7A"],
        "hp": ["00:1A:4B", "00:1B:78", "00:1E:0B"],
        "asus": ["00:1A:92", "00:1E:8C", "00:1F:3A"],
        "lenovo": ["00:1C:25", "00:1D:72", "00:1F:29"],
        "acer": ["00:1A:80", "00:1B:D0", "00:1D:0F"],
        "toshiba": ["00:1D:36", "00:1E:33", "00:1F:3B"],
        "random": ["02:00:00", "02:1A:2B", "02:3C:4D"]
    }
    
    prefix = vendors.get(vendor_name.lower(), ["02:00:00"])
    prefix = random.choice(prefix)
    suffix = ":".join([f"{random.randint(0,255):02x}" for _ in range(3)])
    return f"{prefix}:{suffix}"

def generate_random_mac():
    """Генерация случайного MAC-адреса"""
    first = random.choice(['02', '04', '06', '08', '0A', '0C', '0E'])
    rest = ':'.join([f"{random.randint(0,255):02x}" for _ in range(5)])
    return f"{first}:{rest}"

# ==================== СОХРАНЕНИЕ И ВОССТАНОВЛЕНИЕ ====================

def save_original_mac(interface, mac):
    """Сохранение оригинального MAC-адреса"""
    try:
        os.makedirs("/tmp/mac_spoofer", exist_ok=True)
        with open(f"/tmp/mac_spoofer/original_mac_{interface}.txt", "w") as f:
            f.write(mac)
        print_colored(f"✓ Оригинальный MAC сохранён: {mac}", Colors.GREEN)
        return True
    except Exception as e:
        print_colored(f"✗ Ошибка сохранения MAC: {e}", Colors.RED)
        return False

def restore_mac(interface):
    """Восстановление оригинального MAC-адреса"""
    try:
        with open(f"/tmp/mac_spoofer/original_mac_{interface}.txt", "r") as f:
            original_mac = f.read().strip()
        if original_mac:
            return set_new_mac(interface, original_mac)
    except FileNotFoundError:
        print_colored("✗ Файл с оригинальным MAC не найден", Colors.RED)
    except Exception as e:
        print_colored(f"✗ Ошибка восстановления: {e}", Colors.RED)
    return False

# ==================== ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ====================

def log_mac_change(interface, old_mac, new_mac, status="success"):
    """Логирование изменений MAC-адреса"""
    log_file = os.path.expanduser("~/.mac_spoofer_history.json")
    try:
        with open(log_file, "r") as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        history = []
    
    history.append({
        "timestamp": datetime.now().isoformat(),
        "os": OS_TYPE,
        "interface": interface,
        "old_mac": old_mac,
        "new_mac": new_mac,
        "status": status
    })
    
    if len(history) > 1000:
        history = history[-1000:]
    
    try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, "w") as f:
            json.dump(history, f, indent=2)
        return True
    except Exception as e:
        print_colored(f"Ошибка логирования: {e}", Colors.RED)
        return False

def show_history():
    """Отображение истории изменений"""
    log_file = os.path.expanduser("~/.mac_spoofer_history.json")
    try:
        with open(log_file, "r") as f:
            history = json.load(f)
        
        print_colored("\n=== ИСТОРИЯ ИЗМЕНЕНИЙ MAC ===\n", Colors.BOLD)
        for entry in history[-20:]:
            status_color = Colors.GREEN if entry['status'] == 'success' else Colors.RED
            print_colored(
                f"{entry['timestamp']} | {entry['os']} | {entry['interface']} | "
                f"{entry['old_mac']} → {entry['new_mac']} | {entry['status']}",
                status_color
            )
    except FileNotFoundError:
        print_colored("История изменений не найдена", Colors.YELLOW)
    except Exception as e:
        print_colored(f"Ошибка чтения истории: {e}", Colors.RED)

def check_mac_availability(mac):
    """Проверка MAC-адреса на конфликты в сети"""
    print_colored(f"Проверка MAC {mac} в сети...", Colors.YELLOW)
    try:
        result = subprocess.check_output(["arp", "-a"]).decode()
        if mac.upper() in result.upper():
            print_colored("⚠ ВНИМАНИЕ: Этот MAC-адрес уже используется в сети!", Colors.RED)
            return False
        else:
            print_colored("✓ MAC-адрес свободен", Colors.GREEN)
            return True
    except:
        print_colored("Не удалось проверить MAC в сети", Colors.YELLOW)
        return True

def spoof_with_animation(interface, new_mac):
    """Смена MAC с анимацией прогресса"""
    print_colored(f"Смена MAC-адреса на {interface}:", Colors.CYAN)
    
    for i in range(101):
        time.sleep(0.02)
        bar = "█" * (i // 2) + "░" * (50 - i // 2)
        print(f"\r[{bar}] {i}%", end="")
    
    print()
    result = set_new_mac(interface, new_mac)
    if result:
        print_colored("✅ MAC изменён успешно!", Colors.GREEN)
    else:
        print_colored("❌ Ошибка изменения MAC!", Colors.RED)
    return result

# ==================== GUI ИНТЕРФЕЙС ====================

class MacSpooferGUI:
    """Графический интерфейс для MacSpoofer"""
    
    def __init__(self):
        if not TKINTER_AVAILABLE:
            print_colored("Tkinter не установлен. Используйте терминальный режим.", Colors.RED)
            return
        
        self.root = tk.Tk()
        self.root.title(f"MacSpoofer Pro v4.0 - {OS_TYPE.upper()}")
        self.root.geometry("750x650")
        self.root.resizable(True, True)
        
        style = ttk.Style()
        style.theme_use('clam')
        
        # Информация об ОС
        info_label = tk.Label(self.root, text=f"Операционная система: {OS_TYPE.upper()}", 
                             font=("Arial", 10), fg="#666")
        info_label.pack(pady=5)
        
        title_label = tk.Label(self.root, text="MacSpoofer Pro v4.0", 
                               font=("Arial", 16, "bold"), fg="#2196F3")
        title_label.pack(pady=5)
        
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        self.mac_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.mac_tab, text="Управление MAC")
        self.setup_mac_tab()
        
        self.scan_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.scan_tab, text="Сканирование сети")
        self.setup_scan_tab()
        
        self.history_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.history_tab, text="История")
        self.setup_history_tab()
        
        self.root.mainloop()
    
    def setup_mac_tab(self):
        mac_frame = ttk.Frame(self.mac_tab, padding="10")
        mac_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(mac_frame, text="Сетевой интерфейс:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.interface_var = tk.StringVar()
        self.interface_combo = ttk.Combobox(mac_frame, textvariable=self.interface_var, 
                                           state="readonly", width=35)
        self.interface_combo.grid(row=0, column=1, sticky=tk.W, pady=5)
        self.update_interfaces()
        
        ttk.Label(mac_frame, text="Текущий MAC:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.current_mac_label = ttk.Label(mac_frame, text="", font=("Courier", 10))
        self.current_mac_label.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(mac_frame, text="Новый MAC:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.new_mac_var = tk.StringVar()
        self.new_mac_entry = ttk.Entry(mac_frame, textvariable=self.new_mac_var, width=35)
        self.new_mac_entry.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        btn_frame = ttk.Frame(mac_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Применить MAC", command=self.apply_mac).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Случайный MAC", command=self.generate_random).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Восстановить", command=self.restore_mac).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Обновить", command=self.update_interfaces).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(mac_frame, text="Вендор:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.vendor_var = tk.StringVar()
        vendors = ["apple", "intel", "samsung", "dell", "cisco", "hp", "asus", "lenovo", "acer", "toshiba", "random"]
        self.vendor_combo = ttk.Combobox(mac_frame, textvariable=self.vendor_var, 
                                        values=vendors, state="readonly", width=20)
        self.vendor_combo.grid(row=4, column=1, sticky=tk.W, pady=5)
        self.vendor_combo.set("random")
        ttk.Button(mac_frame, text="По вендору", 
                  command=self.generate_by_vendor).grid(row=4, column=2, padx=5)
    
    def setup_scan_tab(self):
        scan_frame = ttk.Frame(self.scan_tab, padding="10")
        scan_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(scan_frame, text="Интерфейс:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.scan_interface_var = tk.StringVar()
        self.scan_interface_combo = ttk.Combobox(scan_frame, textvariable=self.scan_interface_var, 
                                                state="readonly", width=35)
        self.scan_interface_combo.grid(row=0, column=1, sticky=tk.W, pady=5)
        self.update_scan_interfaces()
        
        btn_scan_frame = ttk.Frame(scan_frame)
        btn_scan_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_scan_frame, text="Сканировать сеть", 
                  command=self.scan_network).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_scan_frame, text="Обновить", 
                  command=self.update_scan_interfaces).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_scan_frame, text="Сохранить", 
                  command=self.save_scan_results).pack(side=tk.LEFT, padx=5)
        
        self.scan_results_text = scrolledtext.ScrolledText(scan_frame, height=15, width=80, font=("Courier", 9))
        self.scan_results_text.grid(row=2, column=0, columnspan=2, pady=10)
    
    def setup_history_tab(self):
        history_frame = ttk.Frame(self.history_tab, padding="10")
        history_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(history_frame, text="Показать историю", 
                  command=self.show_history).pack(pady=5)
        
        self.history_text = scrolledtext.ScrolledText(history_frame, height=20, width=80, font=("Courier", 9))
        self.history_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.show_history()
    
    def show_history(self):
        self.history_text.delete(1.0, tk.END)
        log_file = os.path.expanduser("~/.mac_spoofer_history.json")
        try:
            with open(log_file, "r") as f:
                history = json.load(f)
            
            self.history_text.insert(tk.END, "=== ИСТОРИЯ ИЗМЕНЕНИЙ ===\n\n")
            for entry in history[-30:]:
                self.history_text.insert(tk.END, 
                    f"{entry['timestamp']}\n"
                    f"  ОС: {entry.get('os', 'unknown')}\n"
                    f"  Интерфейс: {entry['interface']}\n"
                    f"  {entry['old_mac']} → {entry['new_mac']}\n"
                    f"  Статус: {entry['status']}\n"
                    f"{'-'*50}\n")
        except:
            self.history_text.insert(tk.END, "История не найдена")
    
    def update_interfaces(self):
        interfaces = get_network_interfaces()
        self.interface_combo['values'] = interfaces
        if interfaces:
            self.interface_combo.set(interfaces[0])
            self.update_info()
    
    def update_scan_interfaces(self):
        interfaces = get_network_interfaces()
        self.scan_interface_combo['values'] = interfaces
        if interfaces:
            self.scan_interface_combo.set(interfaces[0])
    
    def update_info(self):
        interface = self.interface_var.get()
        if interface:
            mac = get_current_mac(interface)
            self.current_mac_label.config(text=mac)
    
    def apply_mac(self):
        interface = self.interface_var.get()
        new_mac = self.new_mac_var.get()
        if interface and new_mac:
            old_mac = get_current_mac(interface)
            if set_new_mac(interface, new_mac):
                log_mac_change(interface, old_mac, new_mac)
                save_original_mac(interface, old_mac)
                self.update_info()
                messagebox.showinfo("Успех", f"MAC изменён на {new_mac}")
            else:
                messagebox.showerror("Ошибка", "Не удалось изменить MAC")
        else:
            messagebox.showwarning("Предупреждение", "Выберите интерфейс и введите MAC")
    
    def generate_random(self):
        new_mac = generate_random_mac()
        self.new_mac_var.set(new_mac)
    
    def generate_by_vendor(self):
        vendor = self.vendor_var.get()
        new_mac = generate_mac_by_vendor(vendor)
        self.new_mac_var.set(new_mac)
    
    def restore_mac(self):
        interface = self.interface_var.get()
        if interface:
            if restore_mac(interface):
                self.update_info()
                messagebox.showinfo("Успех", "MAC восстановлен")
            else:
                messagebox.showerror("Ошибка", "Не удалось восстановить MAC")
    
    def scan_network(self):
        interface = self.scan_interface_var.get()
        self.scan_results_text.delete(1.0, tk.END)
        self.scan_results_text.insert(tk.END, "Сканирование сети...\n")
        self.scan_results_text.update()
        
        devices = scan_network(interface if interface else None)
        
        if devices:
            self.scan_results_text.insert(tk.END, "\n" + "="*80 + "\n")
            self.scan_results_text.insert(tk.END, "НАЙДЕННЫЕ УСТРОЙСТВА:\n")
            self.scan_results_text.insert(tk.END, "="*80 + "\n")
            self.scan_results_text.insert(tk.END, f"{'IP-адрес':<20} {'MAC-адрес':<20} {'Производитель':<25}\n")
            self.scan_results_text.insert(tk.END, "-"*80 + "\n")
            
            for device in devices:
                self.scan_results_text.insert(tk.END, 
                    f"{device.get('ip', 'Unknown'):<20} "
                    f"{device.get('mac', 'Unknown'):<20} "
                    f"{device.get('vendor', 'Unknown'):<25}\n"
                )
            
            self.scan_results_text.insert(tk.END, "="*80 + "\n")
            self.scan_results_text.insert(tk.END, f"Всего найдено: {len(devices)} устройств\n")
            self.last_scan_results = devices
        else:
            self.scan_results_text.insert(tk.END, "Устройства не найдены или произошла ошибка\n")
    
    def save_scan_results(self):
        if hasattr(self, 'last_scan_results') and self.last_scan_results:
            save_scan_results(self.last_scan_results)
        else:
            messagebox.showwarning("Предупреждение", "Сначала выполните сканирование")

# ==================== ИНТЕРАКТИВНОЕ МЕНЮ ====================

def interactive_menu():
    """Интерактивное меню для терминального режима"""
    print_colored(f"\n💻 Операционная система: {OS_TYPE.upper()}", Colors.CYAN)
    
    while True:
        print_colored("\n" + "="*50, Colors.BOLD)
        print_colored("   MacSpoofer Pro v4.0 - Главное меню", Colors.BLUE)
        print_colored("="*50, Colors.BOLD)
        print("1. 📡 Показать интерфейсы")
        print("2. 🔄 Сменить MAC (случайный)")
        print("3. 🏭 Сменить MAC (по вендору)")
        print("4. 📝 Сменить MAC (вручную)")
        print("5. ↩️  Восстановить MAC")
        print("6. 📋 Показать историю")
        print("7. 🔍 Сканировать сеть")
        print("8. 🖥️  Графический интерфейс")
        print("0. 🚪 Выход")
        print_colored("="*50, Colors.BOLD)
        
        choice = input("Выберите действие: ")
        
        if choice == "0":
            print_colored("До свидания! 👋", Colors.GREEN)
            break
        
        elif choice == "1":
            interfaces = get_network_interfaces()
            print_colored("\n📡 Доступные интерфейсы:", Colors.YELLOW)
            for intf in interfaces:
                mac = get_current_mac(intf)
                ip = get_ip_address(intf)
                print(f"  • {intf}: MAC={mac}, IP={ip if ip else 'нет IP'}")
        
        elif choice == "2":
            interfaces = get_network_interfaces()
            if not interfaces:
                print_colored("❌ Интерфейсы не найдены", Colors.RED)
                continue
            
            print_colored("\nВыберите интерфейс:", Colors.YELLOW)
            for i, intf in enumerate(interfaces):
                mac = get_current_mac(intf)
                print(f"  {i+1}. {intf} (MAC: {mac})")
            
            idx = input("Номер интерфейса: ")
            try:
                interface = interfaces[int(idx)-1]
                new_mac = generate_random_mac()
                old_mac = get_current_mac(interface)
                
                if spoof_with_animation(interface, new_mac):
                    log_mac_change(interface, old_mac, new_mac)
                    save_original_mac(interface, old_mac)
                    
            except:
                print_colored("❌ Неверный выбор", Colors.RED)
        
        elif choice == "3":
            vendors = ["apple", "intel", "samsung", "dell", "cisco", "hp", "asus", "lenovo", "acer"]
            print_colored("\nДоступные вендоры:", Colors.YELLOW)
            for i, v in enumerate(vendors):
                print(f"  {i+1}. {v}")
            
            idx = input("Выберите вендора: ")
            try:
                vendor = vendors[int(idx)-1]
                new_mac = generate_mac_by_vendor(vendor)
                print_colored(f"🏭 Сгенерирован MAC для {vendor}: {new_mac}", Colors.CYAN)
                
                interfaces = get_network_interfaces()
                if not interfaces:
                    print_colored("❌ Интерфейсы не найдены", Colors.RED)
                    continue
                
                print_colored("\nВыберите интерфейс:", Colors.YELLOW)
                for i, intf in enumerate(interfaces):
                    mac = get_current_mac(intf)
                    print(f"  {i+1}. {intf} (MAC: {mac})")
                
                idx2 = input("Номер интерфейса: ")
                interface = interfaces[int(idx2)-1]
                old_mac = get_current_mac(interface)
                
                if set_new_mac(interface, new_mac):
                    log_mac_change(interface, old_mac, new_mac)
                    save_original_mac(interface, old_mac)
                    print_colored("✅ MAC изменён!", Colors.GREEN)
                else:
                    print_colored("❌ Ошибка изменения MAC", Colors.RED)
                    
            except:
                print_colored("❌ Неверный выбор", Colors.RED)
        
        elif choice == "4":
            interfaces = get_network_interfaces()
            if not interfaces:
                print_colored("❌ Интерфейсы не найдены", Colors.RED)
                continue
            
            print_colored("\nВыберите интерфейс:", Colors.YELLOW)
            for i, intf in enumerate(interfaces):
                mac = get_current_mac(intf)
                print(f"  {i+1}. {intf} (MAC: {mac})")
            
            idx = input("Номер интерфейса: ")
            try:
                interface = interfaces[int(idx)-1]
                new_mac = input("Введите новый MAC (формат: XX:XX:XX:XX:XX:XX): ")
                
                if re.match(r'^[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}$', new_mac):
                    old_mac = get_current_mac(interface)
                    if set_new_mac(interface, new_mac):
                        log_mac_change(interface, old_mac, new_mac)
                        save_original_mac(interface, old_mac)
                        print_colored("✅ MAC изменён!", Colors.GREEN)
                    else:
                        print_colored("❌ Ошибка изменения MAC", Colors.RED)
                else:
                    print_colored("❌ Неверный формат MAC", Colors.RED)
            except:
                print_colored("❌ Неверный выбор", Colors.RED)
        
        elif choice == "5":
            interfaces = get_network_interfaces()
            if not interfaces:
                print_colored("❌ Интерфейсы не найдены", Colors.RED)
                continue
            
            print_colored("\nВыберите интерфейс для восстановления:", Colors.YELLOW)
            for i, intf in enumerate(interfaces):
                print(f"  {i+1}. {intf}")
            
            idx = input("Номер интерфейса: ")
            try:
                interface = interfaces[int(idx)-1]
                restore_mac(interface)
            except:
                print_colored("❌ Неверный выбор", Colors.RED)
        
        elif choice == "6":
            show_history()
        
        elif choice == "7":
            print_colored("\nСканирование сети...", Colors.CYAN)
            devices = scan_network()
            display_network_devices(devices)
            if devices:
                save = input("Сохранить результаты? (y/n): ")
                if save.lower() == 'y':
                    save_scan_results(devices)
        
        elif choice == "8":
            if TKINTER_AVAILABLE:
                print_colored("Запуск графического интерфейса...", Colors.GREEN)
                MacSpooferGUI()
            else:
                print_colored("Tkinter не установлен", Colors.RED)
        
        else:
            print_colored("❌ Неверный выбор", Colors.RED)
        
        input("\nНажмите Enter для продолжения...")

# ==================== ОСНОВНАЯ ФУНКЦИЯ ====================

def main():
    """Главная функция"""
    
    # Проверка прав администратора
    if os.geteuid() != 0 and not IS_WINDOWS:
        print_colored("❌ Запустите скрипт с правами администратора (sudo)!", Colors.RED)
        print_colored("Пример: sudo python3 mac_spoofer.py", Colors.YELLOW)
        sys.exit(1)
    
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(description="MacSpoofer Pro v4.0")
    parser.add_argument("-g", "--gui", action="store_true", help="Запуск в графическом режиме")
    parser.add_argument("-i", "--interface", help="Интерфейс для изменения")
    parser.add_argument("-m", "--mac", help="Новый MAC-адрес")
    parser.add_argument("-r", "--random", action="store_true", help="Сгенерировать случайный MAC")
    parser.add_argument("-v", "--vendor", help="Вендор для генерации MAC")
    parser.add_argument("--restore", action="store_true", help="Восстановить оригинальный MAC")
    parser.add_argument("--history", action="store_true", help="Показать историю")
    parser.add_argument("--scan", action="store_true", help="Сканировать сеть")
    parser.add_argument("--save-scan", help="Сохранить результаты сканирования")
    parser.add_argument("--list", action="store_true", help="Показать интерфейсы")
    
    args = parser.parse_args()
    
    # Обработка аргументов
    if args.gui:
        if TKINTER_AVAILABLE:
            MacSpooferGUI()
        else:
            print_colored("Tkinter не установлен", Colors.RED)
        return
    
    if args.history:
        show_history()
        return
    
    if args.list:
        interfaces = get_network_interfaces()
        print_colored("\n📡 Доступные интерфейсы:", Colors.YELLOW)
        for intf in interfaces:
            mac = get_current_mac(intf)
            ip = get_ip_address(intf)
            print(f"  • {intf}: MAC={mac}, IP={ip if ip else 'нет IP'}")
        return
    
    if args.scan:
        devices = scan_network(args.interface)
        display_network_devices(devices)
        if args.save_scan and devices:
            save_scan_results(devices, args.save_scan)
        return
    
    if args.restore:
        if args.interface:
            restore_mac(args.interface)
        else:
            print_colored("Укажите интерфейс с помощью -i", Colors.RED)
        return
    
    if args.interface:
        if args.mac:
            if re.match(r'^[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}$', args.mac):
                old_mac = get_current_mac(args.interface)
                if set_new_mac(args.interface, args.mac):
                    log_mac_change(args.interface, old_mac, args.mac)
                    save_original_mac(args.interface, old_mac)
                    print_colored(f"✅ MAC изменён на {args.mac}", Colors.GREEN)
                else:
                    print_colored("❌ Ошибка изменения MAC", Colors.RED)
            else:
                print_colored("Некорректный формат MAC", Colors.RED)
        elif args.random:
            new_mac = generate_random_mac()
            old_mac = get_current_mac(args.interface)
            if set_new_mac(args.interface, new_mac):
                log_mac_change(args.interface, old_mac, new_mac)
                save_original_mac(args.interface, old_mac)
                print_colored(f"✅ MAC изменён на {new_mac}", Colors.GREEN)
            else:
                print_colored("❌ Ошибка изменения MAC", Colors.RED)
        elif args.vendor:
            new_mac = generate_mac_by_vendor(args.vendor)
            old_mac = get_current_mac(args.interface)
            if set_new_mac(args.interface, new_mac):
                log_mac_change(args.interface, old_mac, new_mac)
                save_original_mac(args.interface, old_mac)
                print_colored(f"✅ MAC изменён на {new_mac} (вендор: {args.vendor})", Colors.GREEN)
            else:
                print_colored("❌ Ошибка изменения MAC", Colors.RED)
        else:
            print_colored("Укажите новый MAC, используйте --random или --vendor", Colors.RED)
        return
    
    # Интерактивный режим
    interactive_menu()

if __name__ == "__main__":
    main()
