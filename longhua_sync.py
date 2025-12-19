import os
import re
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LonghuaCrawler:
    def __init__(self):
        self.base_url = "https://www.ofiii.com/channel/watch/"
        self.channels = {
            'lhtv01': {'name': '龙华卡通', 'slug': 'litv-longturn01'},
            'lhtv02': {'name': '龙华洋片', 'slug': 'litv-longturn02'},
            'lhtv03': {'name': '龙华电影', 'slug': 'litv-longturn03'},
            'lhtv04': {'name': '龙华日韩', 'slug': 'litv-longturn11'},
            'lhtv05': {'name': '龙华偶像', 'slug': 'litv-longturn12'},
            'lhtv06': {'name': '龙华戏剧', 'slug': 'litv-longturn18'},
            'lhtv07': {'name': '龙华经典', 'slug': 'litv-longturn21'},
        }

    def setup_driver(self):
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        # 核心：排除本地通讯代理，防止卡死
        os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
        
        # 临时清空代理以下载驱动
        old_proxy = os.environ.get('HTTPS_PROXY')
        os.environ['HTTPS_PROXY'] = ''
        service = Service(ChromeDriverManager().install())
        os.environ['HTTPS_PROXY'] = old_proxy if old_proxy else ''

        # 设置浏览器爬虫代理
        if old_proxy:
            options.add_argument(f'--proxy-server={old_proxy}')
        
        driver = webdriver.Chrome(service=service, options=options)
        return driver

    def run(self):
        driver = self.setup_driver()
        results = {}
        try:
            for cid, info in self.channels.items():
                logger.info(f"正在抓取: {info['name']}")
                driver.get(f"{self.base_url}{info['slug']}")
                time.sleep(15) # 等待渲染
                
                # 尝试从 Nuxt 变量提取 ID
                aid = driver.execute_script("try { return window.__NUXT__.data[0].channelInfo.assetId; } catch(e) { return null; }")
                
                if not aid: # 正则匹配兜底
                    match = re.search(r'"assetId"\s*:\s*"([^"]+)"', driver.page_source)
                    aid = match.group(1) if match else None
                
                if aid:
                    logger.info(f"✅ 成功: {aid}")
                    results[cid] = {"name": info['name'], "key": aid}
                else:
                    logger.warning(f"❌ 失败")
            
            self.save(results)
        finally:
            driver.quit()

    def save(self, results):
        if not results: return
        with open("workers.js", "r", encoding="utf-8") as f:
            content = f.read()
        for cid, data in results.items():
            pattern = rf'"{cid}":\s*\{{\s*name:\s*"[^"]+",\s*key:\s*"[^"]*"'
            replacement = f'"{cid}": {{ name: "{data["name"]}", key: "{data["key"]}"'
            content = re.sub(pattern, replacement, content)
        with open("workers.js", "w", encoding="utf-8") as f:
            f.write(content)

if __name__ == "__main__":
    LonghuaCrawler().run()
