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
            
            # 等待时间加长至 15 秒，确保异步脚本执行完毕
            time.sleep(15) 
            
            # 打印当前标题，帮助排查是否被防火墙拦截
            logger.info(f"正在读取页面: {driver.title}")

            # --- 策略 A: 深度 JS 变量提取 ---
            # 遍历所有可能的 Nuxt 数据路径
            asset_id = driver.execute_script("""
                try {
                    const data = window.__NUXT__;
                    if (!data) return null;
                    
                    // 路径 1: 常见频道信息路径
                    if (data.data && data.data[0] && data.data[0].channelInfo) {
                        return data.data[0].channelInfo.assetId;
                    }
                    // 路径 2: 备选状态路径
                    if (data.state && data.state.channel && data.state.channel.current) {
                        return data.state.channel.current.assetId;
                    }
                    // 路径 3: 暴力搜索整个 data 对象中的 assetId 键
                    const findKey = (obj, key) => {
                        if (obj && typeof obj === 'object') {
                            if (obj.hasOwnProperty(key)) return obj[key];
                            for (let k in obj) {
                                let res = findKey(obj[k], key);
                                if (res) return res;
                            }
                        }
                        return null;
                    };
                    return findKey(data, 'assetId');
                } catch(e) { return null; }
            """)
            
            # --- 策略 B: 增强型正则匹配 ---
            if not asset_id:
                html = driver.page_source
                # 匹配多种可能的 JSON 键值对格式
                patterns = [
                    r'["\']assetId["\']\s*:\s*["\']([^"\']{10,})["\']',
                    r'["\']asset_id["\']\s*:\s*["\']([^"\']{10,})["\']',
                    r'playlist/([a-zA-Z0-9_-]{10,})/master\.m3u8'
                ]
                for p in patterns:
                    match = re.search(p, html)
                    if match:
                        asset_id = match.group(1)
                        break
            
            return asset_id
        except Exception as e:
            logger.error(f"抓取 {slug} 异常: {e}")
            return None
