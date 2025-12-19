#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import re
import time
import json
import logging
from datetime import datetime

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
        """配置浏览器，并处理驱动下载时的代理冲突"""
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')

        # 备份并临时清除环境变量中的代理（防止 webdriver-manager 下载驱动时报错）
        old_http = os.environ.get('HTTP_PROXY')
        old_https = os.environ.get('HTTPS_PROXY')
        os.environ['HTTP_PROXY'] = ''
        os.environ['HTTPS_PROXY'] = ''

        try:
            logger.info("正在获取 ChromeDriver...")
            service = Service(ChromeDriverManager().install())
        finally:
            # 还原代理，供浏览器爬网使用
            if old_http: os.environ['HTTP_PROXY'] = old_http
            if old_https: os.environ['HTTPS_PROXY'] = old_https

        # 设置浏览器爬网时的代理
        proxy = old_https or old_http or "http://127.0.0.1:10808"
        proxy_server = proxy.replace("http://", "").replace("https://", "")
        options.add_argument(f'--proxy-server=http://{proxy_server}')
        logger.info(f"浏览器代理已设置为: {proxy_server}")

        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        return driver

    def fetch_asset_id(self, driver, slug):
        try:
            driver.get(f"{self.base_url}{slug}")
            time.sleep(10) # 龙华频道加载较慢，多等一会
            
            # 优先尝试 JS 注入提取
            asset_id = driver.execute_script("""
                try { return window.__NUXT__.data[0].channelInfo.assetId; } catch(e) { return null; }
            """)
            
            # 正则兜底
            if not asset_id:
                match = re.search(r'"assetId"\s*:\s*"([a-zA-Z0-9_-]{10,})"', driver.page_source)
                asset_id = match.group(1) if match else None
            return asset_id
        except Exception as e:
            logger.error(f"抓取 {slug} 失败: {e}")
            return None

    def run(self):
        driver = self.setup_driver()
        results = {}
        try:
            for cid, info in self.channels.items():
                logger.info(f"正在抓取: {info['name']}")
                aid = self.fetch_asset_id(driver, info['slug'])
                if aid:
                    logger.info(f"✅ 成功: {aid}")
                    results[cid] = {"name": info['name'], "key": aid}
                else:
                    logger.warning(f"❌ 失败")
                time.sleep(2)
            self.save_to_workers(results)
        finally:
            driver.quit()

    def save_to_workers(self, results):
        if not results: return
        with open("workers.js", "r", encoding="utf-8") as f:
            content = f.read()
        for cid, data in results.items():
            pattern = rf'"{cid}":\s*\{{\s*name:\s*"[^"]+",\s*key:\s*"[^"]*"'
            replacement = f'"{cid}": {{ name: "{data["name"]}", key: "{data["key"]}"'
            content = re.sub(pattern, replacement, content)
        with open("workers.js", "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("workers.js 更新完成")

if __name__ == "__main__":
    LonghuaCrawler().run()
