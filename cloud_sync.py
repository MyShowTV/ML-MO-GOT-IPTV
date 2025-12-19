import os
import re
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def get_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # 核心修改：明确指定协议为 socks5
    # GitHub 环境下我们的代理地址是 127.0.0.1:10808
    proxy_addr = "socks5://127.0.0.1:10808"
    options.add_argument(f'--proxy-server={proxy_addr}')
    
    # 忽略证书错误（防止代理抓包干扰）
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-running-insecure-content')

    # 临时关闭环境变量中的代理，只为了下载驱动
    old_proxy = os.environ.get('HTTPS_PROXY')
    os.environ['HTTPS_PROXY'] = ''
    service = Service(ChromeDriverManager().install())
    os.environ['HTTPS_PROXY'] = old_proxy if old_proxy else ''

    return webdriver.Chrome(service=service, options=options)

def main():
    driver = get_driver()
    # 恢复所有频道
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
        # 诊断：确认 IP
        logger.info("🕵️ 正在确认浏览器出口 IP...")
        try:
            driver.get("http://ifconfig.me/ip")
            time.sleep(3)
            ip = driver.find_element(By.TAG_NAME, "body").text
            logger.info(f"🌍 浏览器出口 IP 为: {ip}")
        except:
            logger.warning("⚠️ 无法获取 IP，尝试直接抓取...")

        for cid, slug in channels.items():
            logger.info(f"🔍 正在抓取: {cid} ({slug})")
            url = f"https://www.ofiii.com/channel/watch/{slug}"
            
            try:
                driver.get(url)
                time.sleep(15) # 给页面充足的加载时间
                
                html = driver.page_source
                # 提取 AssetID
                match = re.search(r'["\']assetId["\']\s*:\s*["\']([^"\']{10,})["\']', html)
                
                if match:
                    aid = match.group(1)
                    logger.info(f"✅ 成功获取 ID: {aid}")
                    results[cid] = aid
                else:
                    logger.warning(f"❌ 抓取失败，页面标题: {driver.title}")
                    
            except Exception as e:
                logger.error(f"❌ 发生异常: {e}")

        if results:
            update_workers_js(results)
        else:
            logger.error("🚫 未抓取到任何有效数据，请检查地区限制")
            
    finally:
        driver.quit()

def update_workers_js(results):
    file_path = "workers.js"
    if not os.path.exists(file_path):
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    for cid, aid in results.items():
        # 匹配对应频道的 key 字段并更新
        pattern = rf'"{cid}":\s*\{{\s*name:\s*"[^"]+",\s*key:\s*"[^"]*"'
        replacement = f'"{cid}": {{ name: "龙华频道", key: "{aid}"'
        content = re.sub(pattern, replacement, content)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("🎉 workers.js 文件已自动更新并准备提交")

if __name__ == "__main__":
    main()
