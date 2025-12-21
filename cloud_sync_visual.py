import os, time, re, urllib.parse
from datetime import datetime
import chromedriver_autoinstaller
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class OfiiiVisualSync:
    def __init__(self):
        # 解决凭据报错的核心：URL 编码
        raw_pass = os.getenv('MY_BRD_PASS', 'me6lrg0ysg96').strip()
        self.proxy_user = urllib.parse.quote_plus("brd-customer-hl_739668d7-zone-residential_proxy1-country-tw")
        self.proxy_pass = urllib.parse.quote_plus(raw_pass)
        self.proxy_host = "brd.superproxy.io"
        self.proxy_port = "33335"
        self.worker_file = "workers.js"

    def get_driver(self):
        chromedriver_autoinstaller.install()
        proxy_url = f'http://{self.proxy_user}:{self.proxy_pass}@{self.proxy_host}:{self.proxy_port}'
        
        wire_options = {
            'proxy': {'http': proxy_url, 'https': proxy_url, 'no_proxy': 'localhost,127.0.0.1'},
            'verify_ssl': False
        }
        
        chrome_options = Options()
        chrome_options.add_argument('--headless') # 云端必须
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1280,720')
        chrome_options.add_argument('--ignore-certificate-errors')
        
        return webdriver.Chrome(seleniumwire_options=wire_options, options=chrome_options)

    def run(self):
        driver = self.get_driver()
        channels = {'lhtv01': 'litv-longturn03', 'lhtv02': 'litv-longturn21'}
        results = {}

        print(f"🎬 [可视化监控] 任务启动时间: {datetime.now()}")

        try:
            for cid, slug in channels.items():
                print(f"\n--- 🛰️ 正在进入频道可视化嗅探: {cid} ---")
                driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
                
                # 记录状态 1：加载完成
                driver.save_screenshot(f"1_{cid}_loaded.png")
                print(f"📸 [截图] 页面已加载，保存为 1_{cid}_loaded.png")

                try:
                    wait = WebDriverWait(driver, 30)
                    play_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "vjs-big-play-button")))
                    
                    # 模拟人类点击
                    driver.execute_script("arguments[0].click();", play_btn)
                    print(f"🖱️ [操作] 已点击播放按钮...")
                    
                    # 记录状态 2：点击后画面
                    time.sleep(5)
                    driver.save_screenshot(f"2_{cid}_playing.png")
                    
                    # 流量截获
                    found = False
                    start_wait = time.time()
                    while time.time() - start_wait < 40:
                        for req in driver.requests:
                            if req.response and 'playlist' in req.url and 'avc1' in req.url:
                                match = re.search(r'playlist/([a-zA-Z0-9_-]+/[^?#\s]+)', req.url)
                                if match:
                                    res = match.group(1)
                                    print(f"🎯 [捕获成功] {cid} -> {res}")
                                    results[cid] = res
                                    found = True; break
                        if found: break
                        time.sleep(3)
                    
                    if not found:
                        print(f"⚠️ [捕获失败] {cid} 在 40 秒内未产生符合条件的流量包")
                        driver.save_screenshot(f"ERR_{cid}_not_found.png")

                except Exception as e:
                    print(f"🔥 [运行时错误] {cid}: {str(e)}")
                    driver.save_screenshot(f"ERR_{cid}_exception.png")

            # 更新文件
            self.save_to_worker(results)
            
        finally:
            driver.quit()

    def save_to_worker(self, results):
        if not results: return
        with open(self.worker_file, "r", encoding="utf-8") as f:
            data = f.read()
        for cid, val in results.items():
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
            data = re.sub(pattern, f'"{cid}": {{ name: "", key: "{val}" }}', data, flags=re.DOTALL)
        with open(self.worker_file, "w", encoding="utf-8") as f:
            f.write(data)
        print(f"\n💾 [存储] 已将 {len(results)} 个新 Key 同步至 {self.worker_file}")

if __name__ == "__main__":
    OfiiiVisualSync().run()
