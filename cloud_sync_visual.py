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
        # 核心修复：对代理账号密码进行编码，解决 Invalid credentials 报错
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
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1280,720')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        return webdriver.Chrome(seleniumwire_options=wire_options, options=chrome_options)

    def run(self):
        driver = self.get_driver()
        channels = {
            'lhtv01': 'litv-longturn03', 'lhtv02': 'litv-longturn21',
            'lhtv03': 'litv-longturn18', 'lhtv04': 'litv-longturn11',
            'lhtv05': 'litv-longturn12', 'lhtv06': 'litv-longturn01',
            'lhtv07': 'litv-longturn02'
        }
        results = {}

        try:
            for cid, slug in channels.items():
                print(f"🔎 正在进入频道: {slug}")
                driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
                time.sleep(5)
                driver.save_screenshot(f"step1_{cid}_load.png") # 截图：加载完成

                try:
                    wait = WebDriverWait(driver, 30)
                    play_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "vjs-big-play-button")))
                    driver.execute_script("arguments[0].click();", play_btn)
                    print(f"▶️ 已触发播放...")
                    time.sleep(8)
                    driver.save_screenshot(f"step2_{cid}_play.png") # 截图：播放中

                    found = False
                    start_wait = time.time()
                    while time.time() - start_wait < 40:
                        for req in driver.requests:
                            if req.response and 'playlist' in req.url and 'avc1' in req.url:
                                match = re.search(r'playlist/([a-zA-Z0-9_-]+/[^?#\s]+)', req.url)
                                if match:
                                    res = match.group(1)
                                    print(f"🎯 捕获成功: {res}")
                                    results[cid] = res
                                    found = True; break
                        if found: break
                        time.sleep(3)
                except Exception as e:
                    print(f"❌ {cid} 抓取异常")
                    driver.save_screenshot(f"error_{cid}.png")

            self.save_to_worker(results)
        finally:
            driver.quit()

    def save_to_worker(self, results):
        if not results: return
        if not os.path.exists(self.worker_file): return
        with open(self.worker_file, "r", encoding="utf-8") as f:
            data = f.read()
        for cid, val in results.items():
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
            data = re.sub(pattern, f'"{cid}": {{ name: "", key: "{val}" }}', data, flags=re.DOTALL)
        with open(self.worker_file, "w", encoding="utf-8") as f:
            f.write(data)
        print(f"💾 数据已同步至 {self.worker_file}")

if __name__ == "__main__":
    OfiiiVisualSync().run()
