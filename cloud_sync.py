import os
import time
import json
import re
from datetime import datetime
import chromedriver_autoinstaller
from seleniumwire import webdriver # 拦截真实网络流量的关键
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class OfiiiDynamicSniper:
    def __init__(self):
        # 你的台湾住宅代理
        self.proxy_host = "brd.superproxy.io"
        self.proxy_port = "33335"
        self.proxy_user = "brd-customer-hl_739668d7-zone-residential_proxy1-country-tw"
        self.proxy_pass = "me6lrg0ysg96"
        
        self.worker_file = "workers.js"
        # 待抓取的频道列表
        self.channels = {
            'lhtv01': 'litv-longturn03',
            'lhtv06': 'litv-longturn01'
        }

    def get_driver(self):
        """配置带代理的真机浏览器"""
        chromedriver_autoinstaller.install()
        
        # Selenium-Wire 专属代理配置
        wire_options = {
            'proxy': {
                'http': f'http://{self.proxy_user}:{self.proxy_pass}@{self.proxy_host}:{self.proxy_port}',
                'https': f'https://{self.proxy_user}:{self.proxy_pass}@{self.proxy_host}:{self.proxy_port}',
                'no_proxy': 'localhost,127.0.0.1'
            }
        }
        
        chrome_options = Options()
        # 调试阶段建议设为 False，能看到浏览器操作；正式运行设为 True
        chrome_options.add_argument('--headless') 
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument("--mute-audio") # 静音运行
        
        return webdriver.Chrome(seleniumwire_options=wire_options, options=chrome_options)

    def sniff_channel(self, cid, slug):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📺 动态抓取开始: {cid} ({slug})")
        driver = self.get_driver()
        
        try:
            # 1. 访问频道页
            driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
            
            # 2. 强力触发播放 (绕过所有覆盖层)
            wait = WebDriverWait(driver, 25)
            print("🖱️ 正在定位播放器...")
            
            # 寻找大播放按钮
            play_btn = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "vjs-big-play-button")))
            driver.execute_script("arguments[0].click();", play_btn)
            print("🚀 已强制点击播放，进入流量拦截模式...")

            # 3. 实时监控网络封包 (监控时长 45 秒，因为广告可能很长)
            start_time = time.time()
            while time.time() - start_time < 45:
                # 遍历浏览器产生的所有请求
                for request in driver.requests:
                    if request.response:
                        url = request.url
                        # 核心过滤逻辑：必须包含 playlist、avc1 和 .m3u8
                        if 'playlist' in url and '.m3u8' in url and 'avc1' in url:
                            print(f"🎯 截获目标 URL: {url}")
                            
                            # 使用正则提取 /playlist/ 后的关键部分
                            # 例如提取: NIySmp86SwI/litv-longturn03-avc1_336000=1-mp4a_114000=2.m3u8
                            match = re.search(r'playlist/([a-zA-Z0-9_-]+/[^?]+)', url)
                            if match:
                                result = match.group(1)
                                print(f"✅ 动态提取成功: {result}")
                                return result
                                
                time.sleep(3)
                print(f"⏳ 正在监听后台流量... ({int(time.time()-start_time)}s)")

            print(f"❌ {cid} 抓取超时，未发现符合条件的 playlist 请求。")
        except Exception as e:
            print(f"🔥 动态抓取异常: {e}")
        finally:
            driver.quit()
            # 必须清除请求历史，防止干扰下一个频道
            # 注意：selenium-wire 会自动清理，但重启 driver 更稳妥
        return None

    def update_worker(self, cid, new_key):
        if not os.path.exists(self.worker_file): return
        with open(self.worker_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 精准替换 workers.js 中的 key
        pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
        replacement = f'"{cid}": {{ name: "", key: "{new_key}" }}'
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        with open(self.worker_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"📝 {cid} 已写入 workers.js")

    def run(self):
        for cid, slug in self.channels.items():
            key = self.sniff_channel(cid, slug)
            if key:
                self.update_worker(cid, key)
            time.sleep(5)

if __name__ == "__main__":
    OfiiiDynamicSniper().run()
