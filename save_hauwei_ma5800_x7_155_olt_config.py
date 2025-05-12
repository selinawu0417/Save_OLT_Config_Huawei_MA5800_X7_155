import paramiko
import time
import re
from datetime import datetime
import sys

OLT_IP = "192.168.164.155"  # 請填寫正確 IP
OLT_PORT = 22
OLT_USER = "adminsqa"
OLT_PASS = "pon1234"
PROMPT = "MA5800-X7#"
MORE_FLAG = "-- More --"
TIMEOUT = 600

def strip_ansi_sequences(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def save_config():
    log_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"huawei_ma5800_config_log_{log_time}.txt"

    try:
        print("[INFO] Connecting to OLT...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(OLT_IP, port=OLT_PORT, username=OLT_USER, password=OLT_PASS,
                    look_for_keys=False, allow_agent=False)

        chan = ssh.invoke_shell()
        time.sleep(1)
        chan.recv(9999)  # 清 welcome 訊息

        # 切換 enable 模式
        chan.send("enable\n")
        time.sleep(1)
        chan.recv(4096)

        # 發送指令
        chan.send("display current-configuration\n")
        time.sleep(2)

        output = ""
        start_time = time.time()

        while True:
            if chan.recv_ready():
                chunk = chan.recv(4096).decode(errors="ignore")
                output += chunk
                print(strip_ansi_sequences(chunk).strip())

                # 如果遇到 -- More -- 則送出空白鍵
                if MORE_FLAG in chunk:
                    chan.send(" ")
                    time.sleep(0.2)
                elif PROMPT in chunk:
                    print("[INFO] Prompt received. Output complete.")
                    break

            if time.time() - start_time > TIMEOUT:
                print("[WARNING] Timeout reached.")
                break

            time.sleep(0.5)

        cleaned_output = strip_ansi_sequences(output)

        with open(log_file, "w", encoding="utf-8") as f:
            f.write(cleaned_output)

        print(f"[INFO] ✅ Saved configuration to {log_file}")
        chan.close()
        ssh.close()

    except Exception as e:
        print(f"[ERROR] ❌ Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    save_config()
