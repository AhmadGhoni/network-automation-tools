import os
import re
from datetime import datetime
from netmiko import (
    ConnectHandler,
    NetMikoTimeoutException,
    NetMikoAuthenticationException,
)
from netmiko.base_connection import BaseConnection
from rich.console import Console

console = Console()


def connect_to_device(creds):
    hostname = creds["hostname"]
    ip = creds["ip"]
    creds = {
        "device_type": creds["device_type"],
        "ip": creds["ip"],
        "username": creds["username"],
        "password": creds["password"],
        "secret": creds["password"],
        "fast_cli": False,
    }

    try:
        device = ConnectHandler(**creds)
        device.enable()
        return device

    except NetMikoTimeoutException:
        with open("connect_error.csv", "a") as file:
            file.write(f"{hostname};{ip};Device Unreachable/SSH not enabled")
        return None

    except NetMikoAuthenticationException:
        with open("connect_error.csv", "a") as file:
            file.write(f"{hostname};{ip};Authentication failure")
        return None


def show_version(conn: BaseConnection, device_type: str):
    data = {}
    try:
        show_ver = conn.send_command("show version", use_textfsm=True)
        if isinstance(show_ver, str) or isinstance(show_ver, dict):
            return {}
        first = show_ver[0]
        hostname = first.get("hostname", "")
        uptime = first.get("uptime", "")
        version = first.get("version", "")

        data = {
            "hostname": hostname,
            "uptime": uptime,
            "version": version,
        }

        return data
    except Exception as e:
        print(f"Errors: {e}")
        return {}


def show_resources(conn: BaseConnection, device_type: str):
    try:
        # cpu, memory = 0, 0

        if "nxos" not in device_type:
            proc_cpu = conn.send_command("show proc cpu")
            proc_mem = conn.send_command("show proc mem sort")
            # env_fan = conn.send_command("show environment fan")
            # env_power = conn.send_command("show environment power", use_textfsm=True)
            # print(env_power)

            r_cpu = re.search(r"\s+five minutes:\s(\d+)%", proc_cpu)
            r_mem = re.search(
                r"Processor Pool Total:\s+(\d+)\s+Used:\s+(\d+)", proc_mem
            )
            cpu_util = f"{r_cpu.group(1)}%" if r_cpu else "0%"
            if r_mem:
                total_ram = int(r_mem.group(1))
                used_ram = int(r_mem.group(2))
                if total_ram > 0:
                    mem_perc = (used_ram / total_ram) * 100
                    mem_util = f"{mem_perc:.2f}%"
            else:
                mem_util = "0%"

            # STORAGE
            sh_dir_output = conn.send_command("dir | sec free")
            r_dir = re.search(
                r"(\d+)\s+bytes\s+total\s+\((\d+)\s+bytes\s+free\)", sh_dir_output
            )

            if r_dir:
                total_storage_bytes = int(r_dir.group(1))
                used_storage_bytes = total_storage_bytes - int(r_dir.group(2))
                if total_storage_bytes > 0:
                    storage_perc = (used_storage_bytes / total_storage_bytes) * 100
                    storage_util = f"{storage_perc:.2f}%"
            else:
                storage_util = "0%"

            return {
                "cpu_utilization": cpu_util,
                "memory_utilization": mem_util,
                "storage_utilization": storage_util,
            }

        system_resources = conn.send_command("show system resources")
        # fan = conn.send_command("show environment fan", use_textfsm=True)
        # power = conn.send_command("show environment power", use_textfsm=True)
        # print(json.dumps(fan, indent=2))
        # print(json.dumps(power, indent=2))

        r_cpu = re.search(
            r"CPU\s+states\s+:\s+([\d.]+)%\s+user,\s+([\d.]+)%\s+kernel",
            system_resources,
        )
        cpu_util = (
            f"{float(r_cpu.group(1)) + float(r_cpu.group(2)):.2f}%" if r_cpu else "0%"
        )

        r_mem = re.search(
            r"Memory usage:\s+(\d+)K\s+total,\s+(\d+)K\sused", system_resources
        )

        if r_mem:
            total_mem = int(r_mem.group(1))
            used_mem = int(r_mem.group(2))
            if total_mem > 0:
                mem_util = f"{(used_mem / total_mem) * 100:.2f}%"
        else:
            mem_util = 0

        # STORAGE
        dir_output = conn.send_command("dir | in bytes")
        r_used = re.search(r"(\d+)\s+bytes\s+used", dir_output)
        r_total = re.search(r"(\d+)\s+bytes\s+total", dir_output)
        used_storage = int(r_used.group(1)) if r_used else 0
        total_storage = int(r_total.group(1)) if r_total else 0
        if total_storage > 0:
            storage_perc = (used_storage / total_storage) * 100
            storage_util = f"{storage_perc:.2f}%"
        else:
            storage_util = "0%"

        return {
            "cpu_utilization": cpu_util,
            "memory_utilization": mem_util,
            "storage_utilization": storage_util,
        }

    except Exception as e:
        print(f"Errors: {e}")
        return {}


def show_interface(conn: BaseConnection, device_type: str):
    try:
        show_interfaces = conn.send_command("show interface", use_textfsm=True)

        # 🔁 Normalize keys so ALL platforms use "protocol_status"
        for item in show_interfaces:
            # if protocol_status is missing, try to fill it from admin_state (NXOS)
            if "protocol_status" not in item or not item.get("protocol_status"):
                item["protocol_status"] = item.get("admin_state", "")

        # ✅ Unified fields for BOTH IOS and NXOS
        fields = [
            "interface",
            "link_status",
            "protocol_status",  # normalized key
            "description",
            "ip_address",
            "prefix_length",
            "mtu",
            "speed",
            "input_errors",
            "output_errors",
            "crc",
        ]

        filtered = [
            {key: item.get(key, "") for key in fields} for item in show_interfaces
        ]

        return filtered

    except Exception as e:
        print(f"Errors: {e}")
        return None


def show_spanning_tree_detail(conn: BaseConnection, device_type: str):
    print("show_version")


def show_spanning_tree_blockedports(conn: BaseConnection, device_type: str):
    print("show_version")


def show_spanning_tree_root(conn: BaseConnection, device_type: str):
    print("show_version")


def show_mac_address_table(conn: BaseConnection, device_type: str):
    try:
        mac_table = conn.send_command("show mac address-table", use_textfsm=True)

        normalized = []

        for item in mac_table:
            entry = {}

            # VLAN is common on both
            entry["vlan_id"] = item.get("vlan_id", "")

            # 🔁 Normalize MAC address key
            entry["mac_address"] = (
                item.get("mac_address") or item.get("destination_address") or ""
            )

            # 🔁 Normalize type
            entry["type"] = item.get("type", "")

            # 🔁 Normalize ports (string in NXOS, list in IOS)
            ports = item.get("ports") or item.get("destination_port") or ""

            # Convert IOS list → "Gi1/0/1"
            if isinstance(ports, list):
                ports = ",".join(ports)

            entry["ports"] = ports

            normalized.append(entry)

        return normalized
    except Exception as e:
        print(f"Errors: {e}")
        return None


def show_ip_route(conn: BaseConnection, device_type: str):
    try:
        routes = []

        if "nxos" in device_type:
            nxos_routes = conn.send_command("show ip route vrf all", use_textfsm=True)

            if not isinstance(nxos_routes, list):
                return []

            for item in nxos_routes:
                routes.append(
                    {
                        "vrf": item.get("vrf", "default"),
                        "protocol": item.get("protocol", ""),
                        "network": item.get("network", ""),
                        "prefix_length": item.get("prefix_length", ""),
                        "nexthop_ip": item.get("nexthop_ip", ""),
                        "nexthop_if": item.get("nexthop_if", ""),
                    }
                )

            return routes

        default_routes = conn.send_command("show ip route", use_textfsm=True)
        if isinstance(default_routes, list):
            for item in default_routes:
                routes.append(
                    {
                        "vrf": "default",
                        "protocol": item.get("protocol", ""),
                        "network": item.get("network", ""),
                        "prefix_length": item.get("prefix_length", ""),
                        "nexthop_ip": item.get("nexthop_ip", ""),
                        "nexthop_if": item.get("nexthop_if", ""),
                    }
                )

        vrfs = conn.send_command("show vrf", use_textfsm=True)

        if not isinstance(vrfs, list):
            return routes

        for vrf in vrfs:
            vrf_name = vrf.get("name")

            if not vrf_name:
                continue

            if vrf_name.lower() == "default":
                continue

            cmd = f"show ip route vrf {vrf_name}"

            vrf_routes = conn.send_command(cmd, use_textfsm=True)

            if not isinstance(vrf_routes, list):
                continue

            for item in vrf_routes:
                routes.append(
                    {
                        "vrf": vrf_name,
                        "protocol": item.get("protocol", ""),
                        "network": item.get("network", ""),
                        "prefix_length": item.get("prefix_length", ""),
                        "nexthop_ip": item.get("nexthop_ip", ""),
                        "nexthop_if": item.get("nexthop_if", ""),
                    }
                )

        return routes

    except Exception as e:
        print(f"Errors: {e}")
        return None


def show_arp(conn: BaseConnection, device_type: str):
    try:
        arp = []

        if "nxos" in device_type:
            nxos_arp = conn.send_command("show ip arp vrf all", use_textfsm=True)

            if not isinstance(nxos_arp, list):
                return []

            for item in nxos_arp:
                arp.append(
                    {
                        "vrf": item.get("vrf", "default"),
                        "ip_address": item.get("ip_address", ""),
                        "mac_address": item.get("mac_address", ""),
                        "interface": item.get("interface", ""),
                    }
                )

            return arp

        default_arp = conn.send_command("show ip arp", use_textfsm=True)
        if isinstance(default_arp, list):
            for item in default_arp:
                arp.append(
                    {
                        "vrf": item.get("vrf", "default"),
                        "ip_address": item.get("ip_address", ""),
                        "mac_address": item.get("mac_address", ""),
                        "interface": item.get("interface", ""),
                    }
                )

        vrfs = conn.send_command("show vrf", use_textfsm=True)

        if not isinstance(vrfs, list):
            return arp

        for vrf in vrfs:
            vrf_name = vrf.get("name")

            if not vrf_name:
                continue

            if vrf_name.lower() == "default":
                continue

            cmd = f"show ip arp vrf {vrf_name}"

            vrf_routes = conn.send_command(cmd, use_textfsm=True)

            if not isinstance(vrf_routes, list):
                continue

            for item in vrf_routes:
                arp.append(
                    {
                        "vrf": vrf_name,
                        "ip_address": item.get("ip_address", ""),
                        "mac_address": item.get("mac_address", ""),
                        "interface": item.get("interface", ""),
                    }
                )

        return arp

    except Exception as e:
        print(f"Errors: {e}")
        return None


def show_logg(conn: BaseConnection, device_type: str):
    try:
        logs = []
        logg = conn.send_command("show logg | in %SYS-5-")
        logs.extend(re.findall(r"%SYS-5-\S+: .*", logg))
        logs.extend(re.findall(r"SYS-5-\S+: .*", logg))

        return logs

    except Exception as e:
        print(f"Errors: {e}")
        return None


def collect_data_mantools(creds):
    hostname = creds["hostname"]
    device_type = creds["device_type"]

    conn = connect_to_device(creds)

    if conn:
        console.print(
            f"[bold cyan]Connected to {hostname} ({device_type})...[/bold cyan]"
        )

        try:
            show_inv = conn.send_command("show inv")
            show_int_des = conn.send_command("show interface description")
            show_int_status = conn.send_command("show interface status")
            show_int_trunk = conn.send_command("show interface trunk")
            show_int = conn.send_command("show interface")
            show_ip_arp = conn.send_command("show ip arp")
            show_mac_address_table = conn.send_command("show mac address-table")
            show_cdp_nei = conn.send_command("show cdp neighbors")
            show_cdp_nei_det = conn.send_command("show cdp neighbors detail")
            show_lldp_nei = conn.send_command("show lldp neighbors")
            show_lldp_nei_det = conn.send_command("show lldp neighbors detail")

            if "nxos" in device_type:
                show_port_channel = conn.send_command("show port-channel summary")
                show_standby = conn.send_command("show hsrp brief")
            else:
                show_port_channel = conn.send_command("show etherchannel summary")
                show_standby = conn.send_command("show standby brief")

            combined = (
                f"{show_inv}\n"
                f"{show_int_des}\n"
                f"{show_int_status}\n"
                f"{show_int_trunk}\n"
                f"{show_int}\n"
                f"{show_ip_arp}\n"
                f"{show_mac_address_table}\n"
                f"{show_cdp_nei}\n"
                f"{show_cdp_nei_det}\n"
                f"{show_lldp_nei}\n"
                f"{show_lldp_nei_det}\n"
                f"{show_port_channel}\n"
                f"{show_standby}\n"
            )

            return combined
        except Exception as e:
            print(f"Errors: {e}")
            return None
    else:
        print(f"ERROR: Failed to capture from {hostname}")


def collect_devices_data(devices, customer_name, base_dir=None):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    if base_dir:
        path = os.path.join(base_dir, "legacy", "mantools", timestamp)
    else:
        path = os.path.join("legacy", "results", "mantools", timestamp)
    os.makedirs(path, exist_ok=True)

    for dev in devices:
        hostname = dev.get("hostname", "")
        data = collect_data_mantools(dev)
        with open(os.path.join(path, f"{hostname}.txt"), "w") as f:
            f.write(data)
