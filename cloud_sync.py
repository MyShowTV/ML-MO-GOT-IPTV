import os
import time
import json
import re
from datetime import datetime
import chromedriver_autoinstaller
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class OfiiiDynamicSync:
    def __init__(self):
        # 住宅代理配置
        self.proxy_host = "brd.superproxy.io"
        self.proxy_port = "33335"
        self.proxy_user = "brd-customer-hl_739668d7-zone-residential_proxy1-country-tw"
        self.proxy_pass = os.getenv('MY_BRD_PASS', 'me6lrg0ysg96') # 优先从加密变量读取
        
        self.worker_file = "workers.js"
        # 需要抓取的频道
        self.channels = {
            'lhtv01': 'litv-longturn03', 'lhtv02': 'litv-longturn21',
            'lhtv03': 'litv-longturn18', 'lhtv04': 'litv-longturn11',
            'lhtv05': 'litv-longturn12', 'lhtv06': 'litv-longturn01',
            'lhtv07': 'litv-longturn02'
        }

    def get_driver(self):
        chromedriver_autoinstaller.install()
        
        wire_options = {
            'proxy': {
                'http': f'http://{self.proxy_user}:{self.proxy_pass}@{self.proxy_host}:{self.proxy_port}',
                'https': f'https://{self.proxy_user}:{self.proxy_pass}@{self.proxy_host}:{self.proxy_port}',
                'no_proxy': 'localhost,127.0.0.1'
            },
            'verify_ssl': False
        }
        
        chrome_options = Options()
        chrome_options.add_argument('--headless') # Actions环境必须开启
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--mute-audio")
        
        return webdriver.Chrome(seleniumwire_options=wire_options, options=chrome_options)

    def capture_key(self, driver, slug):
        print(f"📡 正在嗅探频道: {slug}")
        try:
            driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
            del driver.requests # 清除旧请求
            
            # 点击播放触发 m3u8 请求
            wait = WebDriverWait(driver, 20)
            play_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "vjs-big-play-button")))
            driver.execute_script("arguments[0].click();", play_btn)
            
            # 等待并拦截
            start_time = time.time()
            while time.time() - start_time < 45:
                for request in driver.requests:
                    if request.response and 'playlist' in request.url and 'avc1' in request.url:
                        # 提取 ID/filename 格式
                        match = re.search(r'playlist/([a-zA-Z0-9_-]+/[^?#\s]+)', request.url)
                        if match:
                            res = match.group(1)
                            print(f"✅ 成功截获: {res}")
                            return res
                time.sleep(3)
        except Exception as e:
            print(f"❌ 抓取失败 {slug}: {str(e)}")
        return None

    def run(self):
        driver = self.get_driver()
        updates = {}
        try:
            for cid, slug in self.channels.items():
                key = self.capture_key(driver, slug)
                if key:
                    updates[cid] = key
                time.sleep(5)
            
            if updates and os.path.exists(self.worker_file):
                with open(self.worker_file, "r", encoding="utf-8") as f:
                    content = f.read()
                for cid, new_key in updates.items():
                    pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
                    content = re.sub(pattern, f'"{cid}": {{ name: "", key: "{new_key}" }}', content, flags=re.DOTALL)
                with open(self.worker_file, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"🚀 已同步 {len(updates)} 个频道到 workers.js")
        finally:
            driver.quit()

if __name__ == "__main__":
    OfiiiDynamicSync().run()
