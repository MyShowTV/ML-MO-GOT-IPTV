import os, re, time
import chromedriver_autoinstaller
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options

def get_asset_id(cid, slug):
    print(f"🔍 正在抓取频道: {cid}...")
    chromedriver_autoinstaller.install()
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--blink-settings=imagesEnabled=false') # 禁用图片省流量
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    sw_options = {
        'proxy': {
            'http': 'http://127.0.0.1:7890',
            'https': 'http://127.0.0.1:7890',
        },
        'connection_timeout': 60
    }

    driver = None
    try:
        driver = webdriver.Chrome(options=options, seleniumwire_options=sw_options)
        driver.set_page_load_timeout(50)
        
        # 访问频道页
        driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
        time.sleep(20) # 给数据中心代理多一点加载时间
        
        # 模拟点击唤醒 JS
        driver.execute_script("document.body.click();")
        time.sleep(5) 

        for request in reversed(driver.requests):
            if '.m3u8' in request.url and ('playlist' in request.url or 'master' in request.url):
                match = re.search(r'playlist/([a-z0-9A-Z_-]+)/', request.url)
                if match:
                    aid = match.group(1)
                    print(f"✨ 发现 AssetID: {cid} -> {aid}")
                    return aid
        print(f"❌ {cid} 未捕获到关键包")
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
        print("✅ 同步成功！")

if __name__ == "__main__":
    main()
