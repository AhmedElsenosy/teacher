import subprocess
from zk import ZK

INTERFACE = "enx00e04c361694"
STATIC_IP = "192.168.1.100/24"
DEVICE_IP = "192.168.1.201"

def configure_network():
    try:
        print(f"🔧 Setting IP address on {INTERFACE}...")
        subprocess.run(["sudo", "ip", "addr", "add", STATIC_IP, "dev", INTERFACE], check=True)
        subprocess.run(["sudo", "ip", "link", "set", INTERFACE, "up"], check=True)
        print("✅ Network interface configured.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to configure network: {e}")
        return False
    return True

def connect_fingerprint():
    zk = ZK(DEVICE_IP, port=4370)
    try:
        conn = zk.connect()
        print("✅ Connected to ZKTeco device")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return None

if __name__ == "__main__":
    if configure_network():
        connect_fingerprint()
