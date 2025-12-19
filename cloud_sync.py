import os
import re
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def get_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # 防止 Selenium 内部通信被代理拦截
    os.environ['NO_PROXY'] = 'localhost,127.0.0.1'

    # 临时关闭代理以下载驱动
    old_proxy = os.environ.get('HTTPS_PROXY')
    os.environ['HTTPS_PROXY'] = ''
    service = Service(ChromeDriverManager().install())
    os.environ['HTTPS_PROXY'] = old_proxy if old_proxy else ''

    # 设置浏览器代理
    if old_proxy:
        options.add_argument(f'--proxy-server={old_proxy}')

    return webdriver.Chrome(service=service, options=options)

def main():
    driver = get_driver()
    # 频道映射表
    channels = {
        'lhtv01': 'litv-longturn01',
        'lhtv02': 'litv-longturn02',
        'lhtv03': 'litv-longturn03',
        'lhtv04': 'litv-longturn11',
        'lhtv05': 'litv-longturn12',
        'lhtv06': 'litv-longturn18',
        'lhtv07': 'litv-longturn21'
    }
    
    results = {}
    
    try:
        for cid, slug in channels.items():
            logger.info(f"🔍 正在抓取: {cid}")
            url = f"https://www.ofiii.com/channel/watch/{slug}"
            
            try:
                driver.get(url)
                time.sleep(10) # 等待页面加载
                
                # 使用正则直接从源码提取 AssetID，不需要性能日志
                html = driver.page_source
                match = re.search(r'["\']assetId["\']\s*:\s*["\']([^"\']{10,})["\']', html)
                
                if match:
                    aid = match.group(1)
                    logger.info(f"✅ 成功: {aid}")
                    results[cid] = aid
                else:
                    logger.warning(f"❌ 失败: 未找到 ID")
                    
            except Exception as e:
                logger.error(f"❌ 错误: {e}")

        # 如果抓到了数据，更新 workers.js
        if results:
            update_workers_js(results)
            
    finally:
        driver.quit()

def update_workers_js(results):
    file_path = "workers.js"
    if not os.path.exists(file_path):
        logger.error("找不到 workers.js 文件")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    for cid, aid in results.items():
        # 替换 key 字段
        pattern = rf'"{cid}":\s*\{{\s*name:\s*"[^"]+",\s*key:\s*"[^"]*"'
        replacement = f'"{cid}": {{ name: "龙华频道", key: "{aid}"'
        content = re.sub(pattern, replacement, content)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("🎉 workers.js 文件更新完成")

if __name__ == "__main__":
    main()
