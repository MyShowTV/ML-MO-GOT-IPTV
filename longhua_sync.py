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
            url = f"{self.base_url}{slug}"
            driver.get(url)
            # 增加等待时间，确保页面渲染完成
            time.sleep(15) 
            
            # --- 诊断：打印页面标题和部分源码 ---
            title = driver.title
            logger.info(f"页面标题: {title}")
            
            # 方案 A: 通过执行 JS 获取 Nuxt 内部变量 (最稳健)
            # 尝试多种可能的路径
            asset_id = driver.execute_script("""
                try {
                    // 路径 1
                    if (window.__NUXT__ && window.__NUXT__.data[0].channelInfo) {
                        return window.__NUXT__.data[0].channelInfo.assetId;
                    }
                    // 路径 2
                    if (window.__NUXT__ && window.__NUXT__.state.channel.current.assetId) {
                        return window.__NUXT__.state.channel.current.assetId;
                    }
                } catch(e) { return null; }
                return null;
            """)
            
            # 方案 B: 暴力正则匹配整个源码
            if not asset_id:
                html = driver.page_source
                # 匹配格式如 "assetId":"LITV123456"
                match = re.search(r'["\']assetId["\']\s*:\s*["\']([^"\']+)["\']', html)
                if match:
                    asset_id = match.group(1)
            
            # 方案 C: 如果还是不行，可能是因为地区限制导致页面没加载出来
            if not asset_id and "ofiii" not in title.lower():
                logger.error("警告：页面标题不含 ofiii，可能被防火墙拦截或重定向")

            return asset_id
        except Exception as e:
            logger.error(f"抓取 {slug} 异常: {e}")
            return None
