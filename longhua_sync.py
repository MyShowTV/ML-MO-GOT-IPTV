#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import re
import time
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    logger.error("缺少依赖，请运行: pip install selenium webdriver-manager")
    sys.exit(1)

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
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # 1. 强制本地通信不走代理，防止 RemoteDisconnected 错误
        os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
        
        # 2. 临时清除环境变量代理以进行驱动下载
        old_http = os.environ.get('HTTP_PROXY')
        old_https = os.environ.get('HTTPS_PROXY')
        os.environ['HTTP_PROXY'] = ''
        os.environ['HTTPS_PROXY'] = ''

        try:
            logger.info("正在安全环境下获取 ChromeDriver...")
            service = Service(ChromeDriverManager().install())
        finally:
            # 还原代理环境变量
            if old_http: os.environ['HTTP_PROXY'] = old_http
            if old_https: os.environ['HTTPS_PROXY'] = old_https

        # 3. 设置 Chrome 浏览器实例的代理（用于访问 ofiii）
        proxy = old_https or old_http or "http://127.0.0.1:10808"
        proxy_server = proxy.replace("http://", "").replace("https://", "")
        options.add_argument(f'--proxy-server=http://{proxy_server}')
        # 告诉 Chrome 浏览器本身也避开本地回环地址
        options.add_argument("--proxy-bypass-list=localhost;127.0.0.1")

        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        return driver

    def fetch_asset_id(self, driver, slug):
        try:
            driver.get(f"{self.base_url}{slug}")
            # 增加等待时间，确保 JS 变量注入完成
            time.sleep(12) 
            
            # 优先从 Nuxt 内部变量提取
            asset_id = driver.execute_script("""
                try { return window.__NUXT__.data[0].channelInfo.assetId; } catch(e) { return null; }
            """)
            
            # 正则兜底提取
            if not asset_id:
                html = driver.page_source
                match = re.search(r'"assetId"\s*:\s*"([a-zA-Z0-9_-]{10,})"', html)
                asset_id = match.group(1) if match else None
            return asset_id
        except Exception as e:
            logger.error(f"抓取 {slug} 异常: {e}")
            return None

    def run(self):
        driver = self.setup_driver()
        results = {}
        try:
            for cid, info in self.channels.items():
                logger.info(f">> 目标: {info['name']}")
                aid = self.fetch_asset_id(driver, info['slug'])
                if aid:
                    logger.info(f"✅ 捕获成功: {aid}")
                    results[cid] = {"name": info['name'], "key": aid}
                else:
                    logger.warning(f"❌ 捕获失败: {info['name']}")
                time.sleep(3)
            self.save_to_workers(results)
        finally:
            driver.quit()

    def save_to_workers(self, results):
        if not results:
            logger.error("无有效数据，取消文件更新")
            return
        
        file_name = "workers.js"
        if not os.path.exists(file_name):
            logger.error(f"找不到 {file_name}")
            return

        with open(file_name, "r", encoding="utf-8") as f:
            content = f.read()

        for cid, data in results.items():
            pattern = rf'"{cid}":\s*\{{\s*name:\s*"[^"]+",\s*key:\s*"[^"]*"'
            replacement = f'"{cid}": {{ name: "{data["name"]}", key: "{data["key"]}"'
            content = re.sub(pattern, replacement, content)

        with open(file_name, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"成功同步至 {file_name}")

if __name__ == "__main__":
    LonghuaCrawler().run()
