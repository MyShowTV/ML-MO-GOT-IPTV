import os
import subprocess
import threading
import time

def start_mihomo():
    print("🚀 启动 Mihomo 隧道...")
    os.system("wget https://github.com/MetaCubeX/Mihomo/releases/download/v1.18.9/mihomo-linux-amd64-v1.18.9.gz -O mihomo.gz")
    os.system("gunzip mihomo.gz && mv mihomo-linux-amd64-v1.18.9 mihomo && chmod +x mihomo")
    os.system("./mihomo -f clash_config.yml &")
    time.sleep(10)
    print("✅ Mihomo 已启动完成。")

def run_crawler():
    print("🕷️ 正在执行 cloud_sync.py ...")
    os.system("python cloud_sync.py")

if __name__ == "__main__":
    threading.Thread(target=start_mihomo).start()
    time.sleep(12)
    run_crawler()
