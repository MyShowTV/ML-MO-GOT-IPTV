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
    # 强制伪装成真实浏览器，避免被部分反爬策略拦截
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    proxy_addr = "socks5://127.0.0.1:10808"
    options.add_argument(f'--proxy-server={proxy_addr}')
    options.add_argument('--ignore-certificate-errors')

    old_proxy = os.environ.get('HTTPS_PROXY')
    os.environ['HTTPS_PROXY'] = ''
    service = Service(ChromeDriverManager().install())
    os.environ['HTTPS_PROXY'] = old_proxy if old_proxy else ''

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
        logger.info(f"🌍 代理确认：{driver.title} (通过 {driver.execute_script('return navigator.userAgent')})")

        for cid, slug in channels.items():
            logger.info(f"🔍 正在抓取: {cid}")
            url = f"https://www.ofiii.com/channel/watch/{slug}"
            
            driver.get(url)
            # 等待时间稍微错开，模拟人为
            time.sleep(15) 
            
            html = driver.page_source
            
            # --- 强化版正则匹配 ---
            # 兼容多种写法：assetId: "xxx" 或 "assetId":"xxx" 或 asset_id 等
            patterns = [
                r'["\']assetId["\']\s*[:=]\s*["\']([^"\']{15,})["\']',
                r'["\']id["\']\s*[:=]\s*["\'](LITV[^"\']+)["\']', # 针对 ofiii 常见的 LITV 开头的 ID
                r'assetId\s*=\s*["\']([^"\']+)["\']'
            ]
            
            found_id = None
            for p in patterns:
                match = re.search(p, html)
                if match:
                    found_id = match.group(1)
                    break
            
            if found_id:
                logger.info(f"✅ 成功获取 {cid}: {found_id}")
                results[cid] = found_id
            else:
                logger.warning(f"❌ {cid} 抓取失败。")
                # 记录页面中所有看起来像 ID 的长字符串（仅前两个，用于调试）
                potential_ids = re.findall(r'LITV[a-zA-Z0-9_-]{5,}', html)
                if potential_ids:
                    logger.info(f"📝 发现疑似 ID 候选词: {list(set(potential_ids))[:3]}")

        if results:
            update_workers_js(results)
            
    finally:
        driver.quit()

def update_workers_js(results):
    file_path = "workers.js"
    if not os.path.exists(file_path): return
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    updated_count = 0
    for cid, aid in results.items():
        # 更新逻辑：匹配 "lhtv01": { ... key: "旧ID" }
        pattern = rf'"{cid}":\s*\{{[^{{}}]+key:\s*"[^"]*"'
        # 保持原来的 name 字段，只替换 key
        if re.search(pattern, content):
            new_pattern_content = re.sub(r'key:\s*"[^"]*"', f'key: "{aid}"', re.search(pattern, content).group())
            content = re.sub(pattern, new_pattern_content, content)
            updated_count += 1

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"🎉 成功更新了 {updated_count} 个频道的 ID")

if __name__ == "__main__":
    main()
