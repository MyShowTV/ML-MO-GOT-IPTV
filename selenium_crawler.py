#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
龙华频道 AssetID 抓取 - Selenium 增强版
专门用于 GitHub Actions 环境
"""

import os
import sys
import re
import time
import json
import logging
from datetime import datetime
from urllib.parse import urljoin

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('selenium_sync.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 导入 Selenium 相关
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    logger.error("缺少 Selenium 依赖，请运行: pip install selenium webdriver-manager")
    sys.exit(1)

class LonghuaSeleniumCrawler:
    def __init__(self, use_proxy=True):
        self.base_url = "https://www.ofiii.com/"
        self.use_proxy = use_proxy
        
        # 频道配置 (使用 slug)
        self.channels = {
            'lhtv01': {'name': '龙华卡通', 'slug': 'litv-longturn01'},
            'lhtv02': {'name': '龙华洋片', 'slug': 'litv-longturn02'},
            'lhtv03': {'name': '龙华电影', 'slug': 'litv-longturn03'},
            'lhtv04': {'name': '龙华日韩', 'slug': 'litv-longturn11'},
            'lhtv05': {'name': '龙华偶像', 'slug': 'litv-longturn12'},
            'lhtv06': {'name': '龙华戏剧', 'slug': 'litv-longturn18'},
            'lhtv07': {'name': '龙华经典', 'slug': 'litv-longturn21'},
        }
    
    def setup_chrome_options(self):
        """配置 Chrome 选项"""
        options = Options()
        
        # GitHub Actions 环境专用配置
        options.add_argument('--headless=new')  # 新版本无头模式
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--window-size=1920,1080')
        
        # 反反爬虫配置
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 真实浏览器指纹
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        options.add_argument(f'user-agent={user_agent}')
        
        # 性能优化
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        
        # 内存优化
        options.add_argument('--memory-pressure-off')
        options.add_argument('--disable-background-timer-throttling')
        
        # 代理设置
        if self.use_proxy and os.environ.get('HTTPS_PROXY'):
            proxy = os.environ.get('HTTPS_PROXY')
            if proxy and '127.0.0.1:7890' in proxy:
                options.add_argument(f'--proxy-server=http://127.0.0.1:7890')
                logger.info("已设置代理: 127.0.0.1:7890")
        
        return options
    
    def get_asset_id(self, channel_slug, retry=2):
        """使用 Selenium 抓取 AssetID"""
        driver = None
        
        for attempt in range(1, retry + 1):
            try:
                logger.info(f"尝试 {attempt}/{retry}: {channel_slug}")
                
                # 配置 Chrome
                options = self.setup_chrome_options()
                
                # 使用 webdriver-manager 自动管理 ChromeDriver
                service = Service()
                driver = webdriver.Chrome(service=service, options=options)
                
                # 注入反检测脚本
                driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [1, 2, 3, 4, 5]
                        });
                        Object.defineProperty(navigator, 'languages', {
                            get: () => ['zh-TW', 'zh', 'en-US', 'en']
                        });
                        window.chrome = {
                            runtime: {},
                            loadTimes: function() {},
                            csi: function() {},
                            app: {}
                        };
                    """
                })
                
                # 构建完整 URL
                url = f"{self.base_url}channel/watch/{channel_slug}"
                logger.info(f"访问: {url}")
                
                driver.get(url)
                
                # 智能等待策略
                wait_times = [5, 10, 15]  # 渐进式等待
                page_loaded = False
                
                for wait_time in wait_times:
                    logger.info(f"等待 {wait_time} 秒...")
                    time.sleep(wait_time)
                    
                    # 检查页面是否正常加载
                    page_source = driver.page_source
                    if len(page_source) > 10000:  # 正常页面源码长度
                        page_loaded = True
                        break
                    elif "404" in page_source or "不存在" in page_source:
                        logger.error("页面返回404错误")
                        break
                
                if not page_loaded:
                    logger.warning(f"页面可能未完全加载，源码长度: {len(page_source)}")
                
                # 获取页面源码
                html = driver.page_source
                
                # 多种模式匹配 AssetID
                patterns = [
                    r'"assetId"\s*:\s*"([a-zA-Z0-9_-]{10,})"',
                    r'playlist/([a-zA-Z0-9_-]{10,})/master\.m3u8',
                    r'asset_id["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                    r'video/playlist/([^/]+)/master',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, html)
                    if match:
                        asset_id = match.group(1)
                        logger.info(f"找到 AssetID: {asset_id[:10]}...")
                        
                        # 验证 AssetID 格式
                        if len(asset_id) >= 10 and re.match(r'^[a-zA-Z0-9_-]+$', asset_id):
                            return asset_id
                
                # 如果没有匹配到，保存页面源码用于调试
                if attempt == retry:
                    debug_file = f"debug_{channel_slug}.html"
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(html[:5000])  # 只保存前5000字符用于调试
                    logger.info(f"调试文件已保存: {debug_file}")
                
            except Exception as e:
                logger.error(f"第 {attempt} 次尝试失败: {e}")
                if attempt < retry:
                    logger.info(f"等待 5 秒后重试...")
                    time.sleep(5)
            finally:
                if driver:
                    driver.quit()
        
        return None
    
    def crawl_all_channels(self):
        """抓取所有频道"""
        results = {}
        success_count = 0
        
        logger.info("=" * 60)
        logger.info("开始抓取所有龙华频道 (Selenium版)")
        logger.info("=" * 60)
        
        for channel_id, channel_info in self.channels.items():
            logger.info(f"处理频道: {channel_info['name']}")
            
            asset_id = self.get_asset_id(channel_info['slug'])
            
            if asset_id:
                results[channel_id] = {
                    'name': channel_info['name'],
                    'slug': channel_info['slug'],
                    'key': asset_id,
                    'type': 'ofiii',
                    'timestamp': int(time.time())
                }
                success_count += 1
                logger.info(f"✅ {channel_info['name']}: 成功")
            else:
                results[channel_id] = {
                    'name': channel_info['name'],
                    'slug': channel_info['slug'],
                    'key': '这里填钥匙',
                    'type': 'ofiii',
                    'timestamp': int(time.time()),
                    'error': '未找到 AssetID'
                }
                logger.warning(f"❌ {channel_info['name']}: 失败")
            
            # 频道间间隔
            if channel_id != list(self.channels.keys())[-1]:
                wait_time = 3
                logger.info(f"等待 {wait_time} 秒后继续...")
                time.sleep(wait_time)
        
        return results, success_count
    
    def update_workers_config(self, results):
        """更新 workers.js 配置"""
        try:
            workers_file = "workers.js"
            if not os.path.exists(workers_file):
                logger.error(f"找不到 {workers_file}")
                return False
            
            with open(workers_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            updated = False
            for channel_id, data in results.items():
                if data.get('key') and data['key'] != '这里填钥匙':
                    # 精确匹配并替换
                    pattern = rf'"{channel_id}":\s*{{\s*name:\s*"[^"]+",\s*key:\s*"[^"]+"'
                    replacement = f'"{channel_id}": {{ name: "{data["name"]}", key: "{data["key"]}"'
                    
                    if re.search(pattern, content):
                        content = re.sub(pattern, replacement, content)
                        updated = True
                        logger.info(f"更新 {data['name']} 配置")
            
            if updated:
                # 备份原文件
                backup_file = f"workers.js.backup.{int(time.time())}"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    with open(workers_file, 'r', encoding='utf-8') as original:
                        f.write(original.read())
                
                # 写入更新
                with open(workers_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                logger.info("✅ workers.js 已更新")
                return True
            
            logger.info("⚠️ 没有需要更新的配置")
            return False
            
        except Exception as e:
            logger.error(f"更新配置文件失败: {e}")
            return False
    
    def save_results(self, results):
        """保存结果到 JSON 文件"""
        timestamp = int(time.time())
        filename = f"longhua_selenium_{timestamp}.json"
        
        data = {
            'timestamp': timestamp,
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'environment': 'selenium',
            'channels': results
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"结果保存到: {filename}")
            return filename
        except Exception as e:
            logger.error(f"保存结果失败: {e}")
            return None

def main():
    """主函数"""
    # 检查是否在代理环境下
    use_proxy = True
    if os.environ.get('HTTPS_PROXY'):
        logger.info("检测到代理设置")
    else:
        logger.warning("未检测到代理设置，可能无法访问")
        use_proxy = False
    
    # 创建抓取器
    crawler = LonghuaSeleniumCrawler(use_proxy=use_proxy)
    
    # 抓取所有频道
    results, success_count = crawler.crawl_all_channels()
    
    # 显示结果
    logger.info("=" * 60)
    logger.info(f"抓取完成: {success_count}/{len(crawler.channels)} 个频道成功")
    logger.info("=" * 60)
    
    # 保存结果
    json_file = crawler.save_results(results)
    
    # 更新 workers.js
    if success_count > 0:
        logger.info("更新 workers.js...")
        crawler.update_workers_config(results)
    else:
        logger.warning("没有成功抓取到 AssetID，跳过更新")
    
    # 显示摘要
    logger.info("结果摘要:")
    for channel_id, data in results.items():
        status = "✅" if data.get('key') and data['key'] != '这里填钥匙' else "❌"
        key_preview = data['key'][:10] + "..." if len(data['key']) > 10 else data['key']
        logger.info(f"  {status} {data['name']}: {key_preview}")
    
    logger.info("=" * 60)
    
    # 返回是否成功
    return success_count > 0

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"脚本执行失败: {e}")
        sys.exit(1)
