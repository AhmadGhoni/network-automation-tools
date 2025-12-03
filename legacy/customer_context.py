# legacy/customer_context.py
# Modul sederhana untuk menyimpan & membaca customer name
# Digunakan GUI untuk memberi konteks customer ke backup, snapshot, dll.

import json
import os

CONFIG_FILE = "customer_config.json"     # EDITABLE AREA: bebas dipindah dir lain

def get_customer_name(default="DEFAULT"):
    """
    Mengambil customer name dari file config.
    Jika tidak ada file, return default.
    """
    if not os.path.exists(CONFIG_FILE):
        return default
    
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
        return data.get("customer_name", default)
    except Exception:
        return default


def set_customer_name(name: str):
    """
    Menyimpan customer name ke file config JSON.
    Akan di-overwrite setiap kali user mengganti customer.
    """
    data = {
        "customer_name": name.strip()
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)
