import paramiko
import time
from datetime import datetime
import re
import sys

OLT_IP = "192.168.164.155"  
OLT_PORT = 22
OLT_USER = "adminsqa"
OLT_PASS = "pon1234"

PROMPT = "MA5800-X7#"
TIMEOUT = 300  # 最多等 5 分鐘

def strip_ansi_sequences(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def save_config():
    log_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"huawei_ma5800_config_log_{log_time}.txt"

    try:
        print(f"[INFO] Connecting to OLT {OLT_IP}...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(OLT_IP, port=OLT_PORT, username=OLT_USER, password=OLT_PASS,
                    look_for_keys=False, allow_agent=False)

        chan = ssh.invoke_shell()
        time.sleep(1)
        chan.recv(9999)  # 清 welcome 訊息

        output = ""
        print(f"[INFO] Sending 'display current-configuration' command...")
        chan.send("display current-configuration\n")

        start_time = time.time()
        while True:
            if chan.recv_ready():
                chunk = chan.recv(4096).decode(errors="ignore")
                output += chunk
                cleaned_chunk = strip_ansi_sequences(chunk)
                print(cleaned_chunk.strip())  # 即時印出

                if PROMPT in chunk:
                    print("[INFO] Complete configuration output received.")
                    break

            if time.time() - start_time > TIMEOUT:
                print(f"[WARNING] Timeout after {TIMEOUT} seconds.")
                break
            time.sleep(1)

        cleaned_output = strip_ansi_sequences(output)

        with open(log_file, "w", encoding="utf-8") as f:
            f.write(cleaned_output)

        print(f"[INFO] ✅ Saved configuration log to {log_file}")
        chan.close()
        ssh.close()

    except Exception as e:
        print(f"[ERROR] ❌ Failed to save configuration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    save_config()
