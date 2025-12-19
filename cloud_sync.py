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
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    proxy_addr = "socks5://127.0.0.1:10808"
    options.add_argument(f'--proxy-server={proxy_addr}')
    options.add_argument('--ignore-certificate-errors')

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def main():
    driver = get_driver()
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
        # 验证代理
        driver.get("http://ifconfig.me/ip")
        logger.info(f"🌍 当前出口 IP: {driver.find_element(By.TAG_NAME, 'body').text}")

        for cid, slug in channels.items():
            logger.info(f"🔍 正在抓取: {cid} ({slug})")
            url = f"https://www.ofiii.com/channel/watch/{slug}"
            
            driver.get(url)
            time.sleep(12) # 等待渲染
            
            # 方法 1: 尝试从页面全局变量中直接读取 (最准确)
            found_id = driver.execute_script("""
                try {
                    return window.__PRELOADED_STATE__.video.programInfo.assetId;
                } catch(e) {
                    return null;
                }
            """)

            # 方法 2: 如果方法 1 失败，使用全网页源码正则搜寻 11 位特征 ID
            if not found_id:
                html = driver.page_source
                # 寻找类似 PKIOGb6cWYI 这种出现在 cdi.ofiii.com 路径中的 ID
                match = re.search(r'/video/playlist/([a-zA-Z0-9_-]{10,12})/', html)
                if match:
                    found_id = match.group(1)
                else:
                    # 备选正则：搜寻 JSON 中的 assetId 字段
                    match_json = re.search(r'["\']assetId["\']\s*:\s*["\']([^"\']+)["\']', html)
                    if match_json:
                        found_id = match_json.group(1)

            if found_id:
                logger.info(f"✅ 成功获取 {cid}: {found_id}")
                results[cid] = found_id
            else:
                logger.warning(f"❌ {cid} 抓取失败，页面标题: {driver.title}")

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
        # 这里假设你的 workers.js 结构是 "lhtv03": { ... key: "PKIOGb6cWYI" }
        # 使用正则精准替换对应 cid 下的 key 字段
        pattern = rf'("{cid}":\s*\{{[^{{}}]+key:\s*")[^"]*"'
        content = re.sub(pattern, rf'\1{aid}"', content)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("🎉 workers.js ID 同步更新完成")

if __name__ == "__main__":
    main()
