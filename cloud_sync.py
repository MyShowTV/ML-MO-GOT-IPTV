import os, re, time
import chromedriver_autoinstaller
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options

def get_asset_id(cid, slug):
    print(f"🔍 正在抓取频道: {cid}...")
    chromedriver_autoinstaller.install()
    
    # --- 你的 Bright Data 代理配置 ---
    # 注意：这里使用了你最新的 datacenter_proxy1 信息
    proxy_auth = 'brd-customer-hl_739668d7-zone-datacenter_proxy1-country-tw:di168nnr7bb9'
    proxy_url = f'http://{proxy_auth}@brd.superproxy.io:33335'

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--blink-settings=imagesEnabled=false') # 省流
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    # 将代理直接注入 selenium-wire
    sw_options = {
        'proxy': {
            'http': proxy_url,
            'https': proxy_url,
            'no_proxy': 'localhost,127.0.0.1'
        },
        'connection_timeout': 60
    }

    driver = None
    try:
        driver = webdriver.Chrome(options=options, seleniumwire_options=sw_options)
        driver.set_page_load_timeout(45)
        
        # 1. 验证 IP (可选，用来在日志里确认国家)
        driver.get('https://geo.brdtest.com/welcome.txt?product=dc&method=native')
        print(f"📡 当前出口节点信息:\n{driver.page_source}")

        # 2. 访问 Ofiii
        driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
        time.sleep(15)
        
        # 扫描网络请求寻找 M3U8
        for request in reversed(driver.requests):
            if '.m3u8' in request.url and ('playlist' in request.url or 'master' in request.url):
                match = re.search(r'playlist/([a-z0-9A-Z_-]+)/', request.url)
                if match:
                    aid = match.group(1)
                    print(f"✨ 成功获取: {cid} -> {aid}")
                    return aid
    except Exception as e:
        print(f"🔥 {cid} 错误: {e}")
    finally:
        if driver: driver.quit()
    return None

def main():
    channels = {
        'lhtv01': 'litv-longturn03', 'lhtv02': 'litv-longturn21',
        'lhtv03': 'litv-longturn18', 'lhtv04': 'litv-longturn11',
        'lhtv05': 'litv-longturn12', 'lhtv06': 'litv-longturn01',
        'lhtv07': 'litv-longturn02'
    }
    
    worker_path = "workers.js"
    with open(worker_path, "r", encoding="utf-8") as f:
        content = f.read()

    updated = False
    for cid, slug in channels.items():
        aid = get_asset_id(cid, slug)
        if aid:
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            updated = True
        time.sleep(3)

    if updated:
        with open(worker_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ 任务完成，数据已同步。")

if __name__ == "__main__":
    main()
