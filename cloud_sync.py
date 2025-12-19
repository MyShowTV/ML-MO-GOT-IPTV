import os
import re
import time
import json
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def get_driver():
    # 隔离驱动下载
    env_copy = os.environ.copy()
    for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'all_proxy', 'ALL_PROXY']:
        if var in os.environ: del os.environ[var]
    driver_path = ChromeDriverManager().install()
    os.environ.update(env_copy)
    
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--proxy-server=socks5://127.0.0.1:10808')
    
    # --- 关键配置：开启性能日志记录 (抓包模式) ---
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    options.add_argument('--disable-blink-features=AutomationControlled')

    return webdriver.Chrome(service=Service(driver_path), options=options)

def extract_id_from_network(driver):
    """
    扫描浏览器所有的网络请求，寻找包含 assetId 的 m3u8 链接
    """
    logs = driver.get_log('performance')
    for entry in logs:
        try:
            message = json.loads(entry['message'])['message']
            if message['method'] == 'Network.requestWillBeSent':
                url = message['params']['request']['url']
                # 寻找包含 playlist 的链接，例如 .../video/playlist/PKIOGb6cWYI/...
                match = re.search(r'video/playlist/([a-zA-Z0-9_-]{11})/', url)
                if match:
                    return match.group(1)
        except:
            continue
    return None

def main():
    channels = {
        'lhtv01': 'litv-longturn01',
        'lhtv02': 'litv-longturn02',
        'lhtv03': 'litv-longturn03',
        'lhtv04': 'litv-longturn11',
        'lhtv05': 'litv-longturn12',
        'lhtv06': 'litv-longturn18',
        'lhtv07': 'litv-longturn21'
    }
    
    driver = get_driver()
    results = {}

    try:
        for cid, slug in channels.items():
            logger.info(f"📡 抓包模式启动: 正在监听 {cid}...")
            driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
            
            # 持续监听 25 秒，期间浏览器会自动请求 m3u8
            found_id = None
            for _ in range(5): # 分段检查，提高效率
                time.sleep(5)
                found_id = extract_id_from_network(driver)
                if found_id: break
            
            if found_id:
                logger.info(f"✨ 成功拦截到 ID: {found_id}")
                results[cid] = found_id
            else:
                logger.warning(f"❌ 监听超时，未发现有效流量")

        if results:
            update_workers_js(results)
    finally:
        driver.quit()

def update_workers_js(results):
    file_path = "workers.js"
    if not os.path.exists(file_path): return
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    for cid, aid in results.items():
        pattern = rf'("{cid}":\s*\{{[^{{}}]+key:\s*")[^"]*"'
        content = re.sub(pattern, rf'\1{aid}"', content)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("🎉 抓包同步完成")

if __name__ == "__main__":
    main()
