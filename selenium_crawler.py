#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
龙华频道 AssetID 抓取 - Selenium 增强终极版
适配本地 v2rayN (10808) 与 GitHub Actions 环境
"""

import os
import sys
import re
import time
import json
import logging
from datetime import datetime

# ================= 配置日志 =================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ================= 导入依赖 =================
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    logger.error("缺少依赖，请执行: pip install selenium webdriver-manager")
    sys.exit(1)

class LonghuaCrawler:
    def __init__(self):
        self.base_url = "https://www.ofiii.com/channel/watch/"
        # 频道配置
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
        """配置并启动无头浏览器"""
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        # 抹除自动化特征
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # --- 智能代理适配 ---
        # 优先读取 GitHub Actions 的环境变量，若无则使用本地 v2rayN 默认端口
        proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')
        if proxy:
            proxy_server = proxy.replace("http://", "").replace("https://", "")
            options.add_argument(f'--proxy-server=http://{proxy_server}')
            logger.info(f"🚀 使用环境代理: {proxy_server}")
        else:
            # 本地 v2rayN 混合端口
            options.add_argument('--proxy-server=http://127.0.0.1:10808')
            logger.info("🏠 使用本地代理: 127.0.0.1:10808")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # 注入 JS 进一步抹除特征
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        return driver

    def fetch_asset_id(self, driver, slug):
        """核心抓取逻辑"""
        url = f"{self.base_url}{slug}"
        try:
            driver.get(url)
            # 等待页面核心元素加载 (最长15秒)
            time.sleep(8) 
            
            # 方案 A: 通过执行 JS 直接从网页的 Nuxt 状态中提取 (最准)
            asset_id = driver.execute_script("""
                try {
                    return window.__NUXT__.data[0].channelInfo.assetId;
                } catch(e) {
                    return null;
                }
            """)
            
            # 方案 B: 正则兜底
            if not asset_id:
                html = driver.page_source
                match = re.search(r'"assetId"\s*:\s*"([a-zA-Z0-9_-]{10,})"', html)
                if match:
                    asset_id = match.group(1)
            
            return asset_id
        except Exception as e:
            logger.error(f"抓取 {slug} 出错: {e}")
            return None

    def run(self):
        driver = self.setup_driver()
        final_results = {}
        
        try:
            for cid, info in self.channels.items():
                logger.info(f"正在处理: {info['name']}...")
                asset_id = self.fetch_asset_id(driver, info['slug'])
                
                if asset_id:
                    logger.info(f"✅ 成功! ID: {asset_id[:12]}...")
                    final_results[cid] = {"name": info['name'], "key": asset_id}
                else:
                    logger.warning(f"❌ 失败: {info['name']}")
                
                time.sleep(2) # 避免请求过快
                
            self.update_workers(final_results)
            
        finally:
            driver.quit()

    def update_workers(self, results):
        """将结果写回 workers.js"""
        if not results:
            logger.error("没有抓取到任何数据，停止更新。")
            return

        file_path = "workers.js"
        if not os.path.exists(file_path):
            logger.error(f"未找到 {file_path}")
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        for cid, data in results.items():
            # 正则替换: 匹配 "cid": { name: "xxx", key: "xxx"
            pattern = rf'"{cid}":\s*\{{\s*name:\s*"[^"]+",\s*key:\s*"[^"]*"'
            replacement = f'"{cid}": {{ name: "{data["name"]}", key: "{data["key"]}"'
            content = re.sub(pattern, replacement, content)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info("🎉 所有 AssetID 已成功同步至 workers.js")

if __name__ == "__main__":
    crawler = LonghuaCrawler()
    crawler.run()
