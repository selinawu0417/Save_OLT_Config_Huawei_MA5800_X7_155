import paramiko
import time
import re
from datetime import datetime
import sys

# === OLT 連線資訊 ===
OLT_IP = "192.168.164.155"
OLT_PORT = 22
OLT_USER = "adminsqa"
OLT_PASS = "pon1234"

PROMPT = "MA5800-X7#"
MORE_FLAG = "-- More"
TIMEOUT = 120

def strip_ansi_sequences(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def save_config():
    log_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"huawei_ma5800_x7_155_olt_save_config_log_{log_time}.txt"

    try:
        print("[INFO] Connecting to OLT...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(OLT_IP, port=OLT_PORT, username=OLT_USER, password=OLT_PASS,
                    look_for_keys=False, allow_agent=False)

        chan = ssh.invoke_shell()
        time.sleep(1)
        chan.recv(9999)  # 清除 welcome 訊息

        # 進入 enable 模式
        chan.send("enable\n")
        time.sleep(1)
        chan.recv(9999)

        # 清 prompt
        chan.send("\n")
        time.sleep(1)
        chan.recv(9999)

        # 發送主命令
        print("[INFO] Sending 'display current-configuration'...")
        chan.send("display current-configuration\n")
        time.sleep(0.5)
        chan.send("\n")
        time.sleep(2)

        output = ""
        start_time = time.time()

        while True:
            if chan.recv_ready():
                chunk = chan.recv(4096).decode(errors="ignore")
                output += chunk
                cleaned_chunk = strip_ansi_sequences(chunk)
                print(cleaned_chunk.strip())

                if PROMPT in chunk:
                    print("[INFO] Prompt received — output complete.")
                    break
                elif MORE_FLAG in chunk:
                    chan.send(" ")
                    time.sleep(0.2)

            if time.time() - start_time > TIMEOUT:
                print("[WARNING] Timeout reached.")
                break

            time.sleep(0.5)

        # 清除 ANSI 及 More 提示
        cleaned_output = strip_ansi_sequences(output)
        cleaned_output = re.sub(r"---- More \( Press 'Q' to break \) ----", "", cleaned_output)

        # 補縮排排版處理
        formatted_lines = []
        for line in cleaned_output.splitlines():
            # 判斷是否需要縮排（不是以關鍵字開頭的指令，表示是被覆蓋顯示的內容）
            if line and not re.match(r"^(port|ont|gem|commit|tcont|quit|omcc|fec|vlan|multicast|xpon|switch|board|sysmode|#)", line):
                formatted_lines.append("    " + line.strip())
            else:
                formatted_lines.append(line.rstrip())

        final_output = "\n".join(formatted_lines)

        with open(log_file, "w", encoding="utf-8") as f:
            f.write(final_output)

        print(f"[INFO] ✅ Configuration saved to {log_file}")
        chan.close()
        ssh.close()

    except Exception as e:
        print(f"[ERROR] ❌ Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    save_config()
