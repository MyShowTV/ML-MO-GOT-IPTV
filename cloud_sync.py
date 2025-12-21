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

class OfiiiFinalSync:
    def __init__(self):
        # 住宅代理配置
        self.proxy_host = "brd.superproxy.io"
        self.proxy_port = "33335"
        self.proxy_user = "brd-customer-hl_739668d7-zone-residential_proxy1-country-tw"
        # 优先读取 GitHub Secrets 中的密码
        self.proxy_pass = os.getenv('MY_BRD_PASS', 'me6lrg0ysg96')
        
        self.worker_file = "workers.js"
        # 频道 ID 对应
        self.channels = {
            'lhtv01': 'litv-longturn03', 'lhtv02': 'litv-longturn21',
            'lhtv03': 'litv-longturn18', 'lhtv04': 'litv-longturn11',
            'lhtv05': 'litv-longturn12', 'lhtv06': 'litv-longturn01',
            'lhtv07': 'litv-longturn02'
        }

    def get_driver(self):
        """初始化配置齐全的浏览器"""
        chromedriver_autoinstaller.install()
        
        wire_options = {
            'proxy': {
                'http': f'http://{self.proxy_user}:{self.proxy_pass}@{self.proxy_host}:{self.proxy_port}',
                'https': f'https://{self.proxy_user}:{self.proxy_pass}@{self.proxy_host}:{self.proxy_port}',
                'no_proxy': 'localhost,127.0.0.1'
            },
            'verify_ssl': False # 必须禁用 SSL 校验以拦截加密流
        }
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--ignore-certificate-errors') # 忽略证书错误
        chrome_options.add_argument('--allow-insecure-localhost')
        chrome_options.add_argument("--mute-audio")
        
        return webdriver.Chrome(seleniumwire_options=wire_options, options=chrome_options)

    def capture_m3u8(self, driver, slug):
        """动态嗅探 m3u8 地址"""
        url = f"https://www.ofiii.com/channel/watch/{slug}"
        print(f"🔎 正在抓取频道: {slug}")
        
        try:
            driver.get(url)
            del driver.requests # 清空之前的历史
            
            # 等待播放按钮并强制点击
            wait = WebDriverWait(driver, 25)
            play_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "vjs-big-play-button")))
            driver.execute_script("arguments[0].click();", play_btn)
            
            # 监听 50 秒（等待广告结束和正片加载）
            start_time = time.time()
            while time.time() - start_time < 50:
                for request in driver.requests:
                    if request.response and 'playlist' in request.url and 'avc1' in request.url:
                        # 提取 key 格式: NIySmp86SwI/litv-longturn03-avc1...m3u8
                        match = re.search(r'playlist/([a-zA-Z0-9_-]+/[^?#\s]+)', request.url)
                        if match:
                            found_key = match.group(1)
                            print(f"🎯 成功捕获 Key: {found_key}")
                            return found_key
                time.sleep(4)
        except Exception as e:
            print(f"⚠️ {slug} 抓取异常: {str(e)}")
        return None

    def run(self):
        driver = self.get_driver()
        results = {}
        
        try:
            for cid, slug in self.channels.items():
                key = self.capture_m3u8(driver, slug)
                if key:
                    results[cid] = key
                time.sleep(3) # 频道间稍微缓冲
            
            if results and os.path.exists(self.worker_file):
                with open(self.worker_file, "r", encoding="utf-8") as f:
                    js_data = f.read()
                
                for cid, new_val in results.items():
                    # 正则匹配并替换 "lhtv01": { ... key: "..." }
                    pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
                    replacement = f'"{cid}": {{ name: "", key: "{new_val}" }}'
                    js_data = re.sub(pattern, replacement, js_data, flags=re.DOTALL)
                
                with open(self.worker_file, "w", encoding="utf-8") as f:
                    f.write(js_data)
                print(f"✨ 任务完成：同步了 {len(results)} 个频道")
        finally:
            driver.quit()

if __name__ == "__main__":
    OfiiiFinalSync().run()
