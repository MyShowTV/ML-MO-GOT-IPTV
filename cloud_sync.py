import os
import time
import json
import re
from datetime import datetime
import chromedriver_autoinstaller
import requests
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 强制禁用不必要的警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class OfiiiDynamicSynchronizer:
    def __init__(self):
        # 住宅代理配置
        self.proxy_host = "brd.superproxy.io"
        self.proxy_port = "33335"
        self.proxy_user = "brd-customer-hl_739668d7-zone-residential_proxy1-country-tw"
        self.proxy_pass = "me6lrg0ysg96"
        
        self.worker_file = "workers.js"
        # 目标频道映射 (cid: slug)
        self.channels = {
            'lhtv01': 'litv-longturn03', 'lhtv02': 'litv-longturn21',
            'lhtv03': 'litv-longturn18', 'lhtv04': 'litv-longturn11',
            'lhtv05': 'litv-longturn12', 'lhtv06': 'litv-longturn01',
            'lhtv07': 'litv-longturn02'
        }

    def get_browser_driver(self):
        """配置并初始化带拦截能力的 Chrome 浏览器"""
        print("📦 正在自动安装/检查 Chromedriver...")
        chromedriver_autoinstaller.install()
        
        # Selenium-Wire 代理配置
        wire_options = {
            'proxy': {
                'http': f'http://{self.proxy_user}:{self.proxy_pass}@{self.proxy_host}:{self.proxy_port}',
                'https': f'https://{self.proxy_user}:{self.proxy_pass}@{self.proxy_host}:{self.proxy_port}',
                'no_proxy': 'localhost,127.0.0.1'
            },
            'verify_ssl': False  # 忽略 SSL 错误以便拦截加密流
        }
        
        chrome_options = Options()
        # GitHub Actions 必须参数
        chrome_options.add_argument('--headless') 
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--mute-audio")
        
        # 模拟真实浏览器 User-Agent
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        chrome_options.add_argument(f'user-agent={ua}')

        return webdriver.Chrome(seleniumwire_options=wire_options, options=chrome_options)

    def sniff_channel_key(self, driver, slug):
        """进入频道页并动态截获 m3u8 密匙"""
        target_url = f"https://www.ofiii.com/channel/watch/{slug}"
        print(f"🌐 正在访问: {target_url}")
        
        try:
            driver.get(target_url)
            # 清除旧请求记录，确保只抓这次点击后的
            del driver.requests
            
            # 1. 等待并点击大的播放按钮
            wait = WebDriverWait(driver, 20)
            play_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "vjs-big-play-button")))
            driver.execute_script("arguments[0].click();", play_btn)
            print("▶️ 已触发播放，正在分析动态网络流量...")

            # 2. 持续轮询网络请求（给广告留出时间）
            start_time = time.time()
            while time.time() - start_time < 50:
                for request in driver.requests:
                    if request.response:
                        url = request.url
                        # 核心匹配逻辑：包含 playlist 且包含 avc1 的 m3u8 地址
                        if 'playlist' in url and '.m3u8' in url and 'avc1' in url:
                            # 提取 /playlist/ 之后的部分
                            match = re.search(r'playlist/([a-zA-Z0-9_-]+/[^?#\s]+)', url)
                            if match:
                                result = match.group(1)
                                print(f"🎯 捕获成功: {result}")
                                return result
                time.sleep(3)
                print(f"⏳ 监听中...已耗时 {int(time.time() - start_time)}s")
            
        except Exception as e:
            print(f"⚠️ 抓取 {slug} 时发生异常: {str(e)}")
        return None

    def update_workers_js(self, updates):
        """将捕获到的新 Key 批量写入 workers.js"""
        if not updates:
            print("💡 没有抓取到任何更新。")
            return
            
        if not os.path.exists(self.worker_file):
            print(f"❌ 找不到文件: {self.worker_file}")
            return

        with open(self.worker_file, "r", encoding="utf-8") as f:
            content = f.read()

        for cid, new_key in updates.items():
            # 使用正则精准替换对应的频道 key
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{new_key}" }}'
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)

        with open(self.worker_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ 成功同步 {len(updates)} 个频道到 {self.worker_file}")

    def run(self):
        driver = self.get_browser_driver()
        all_updates = {}
        
        try:
            for cid, slug in self.channels.items():
                print(f"\n--- 正在处理频道: {cid} ---")
                key = self.sniff_channel_key(driver, slug)
                if key:
                    all_updates[cid] = key
                # 频道间稍微停顿，避免被频率限制
                time.sleep(5)
            
            self.update_workers_js(all_updates)
            
        finally:
            driver.quit()

if __name__ == "__main__":
    OfiiiDynamicSynchronizer().run()
