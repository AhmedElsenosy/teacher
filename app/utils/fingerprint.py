import base64
from zk import ZK
from zk.finger import Finger  # optional, for clarity

def connect_device():
    try:
        zk = ZK('192.168.1.201', port=4370, timeout=5)
        conn = zk.connect()
        return conn
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None

def enroll_fingerprint(uid: int, name: str):
    conn = connect_device()
    if not conn:
        return None

    try:
        conn.disable_device()

        users = conn.get_users()
        user_exists = any(u.uid == uid for u in users)
        if user_exists:
            conn.delete_user(uid=uid)

        # Set user and enroll fingerprint (finger ID = 0)
        conn.set_user(uid=uid, name=name, privilege=0, password='', group_id='', user_id=str(uid))
        conn.enroll_user(uid, 0, 0)

        # Get the fingerprint template
        template = conn.get_user_template(uid, 0)

        if not template:
            print("❌ No fingerprint template retrieved")
            return None

        # Debug output to discover correct attribute
        print(f"📌 Template type: {type(template)}")
        print(f"📌 Template dir: {dir(template)}")

        # Try to extract raw data correctly
        if hasattr(template, "template"):
            raw = template.template
        elif hasattr(template, "serialize"):
            raw = template.serialize()
        elif isinstance(template, str):
            raw = template.encode()
        else:
            raise AttributeError("❌ Unsupported Finger object — no usable attribute found")

        # Encode and return the base64 string
        encoded_template = base64.b64encode(raw).decode()
        return encoded_template

    except Exception as e:
        print(f"❌ Enrollment error: {e}")
        return None

    finally:
        conn.enable_device()
        conn.disconnect()
