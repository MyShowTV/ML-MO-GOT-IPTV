import os, re, time
import chromedriver_autoinstaller
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options

def get_asset_id(cid, slug):
    print(f"🔍 正在探测频道: {cid}...")
    chromedriver_autoinstaller.install()
    
    # --- 代理认证配置 (直接使用你测试成功的 DC 账号) ---
    # 核心：用户名加了 -country-tw 强制锁定台湾
    proxy_user = "brd-customer-hl_739668d7-zone-datacenter_proxy1-country-tw"
    proxy_pass = "di168nnr7bb9"
    proxy_host = "brd.superproxy.io"
    proxy_port = "33335"
    
    proxy_url = f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--blink-settings=imagesEnabled=false') # 禁用图片省流量
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

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
        driver.set_page_load_timeout(60)
        
        # 验证出口 (防止再次跑到美国)
        print("🌍 正在验证代理出口国家...")
        driver.get('https://geo.brdtest.com/mygeo.json')
        print(f"🛰️ 代理返回信息: {driver.page_source}")

        # 抓取 Ofiii
        driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
        time.sleep(20) # 数据中心代理响应慢，多等一会
        
        # 点击页面触发 JS
        driver.execute_script("document.body.click();")
        time.sleep(5)

        for request in reversed(driver.requests):
            if '.m3u8' in request.url and ('playlist' in request.url or 'master' in request.url):
                match = re.search(r'playlist/([a-z0-9A-Z_-]+)/', request.url)
                if match:
                    aid = match.group(1)
                    print(f"✨ 成功获取: {cid} -> {aid}")
                    return aid
        print(f"❌ {cid} 抓取失败：未找到数据流")
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
    if not os.path.exists(worker_path): return

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
        time.sleep(5)

    if updated:
        with open(worker_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ 全部同步完成！")

if __name__ == "__main__":
    main()
