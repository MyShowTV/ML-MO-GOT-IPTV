import os, re, time, json
import chromedriver_autoinstaller
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options

def get_asset_id(cid, slug):
    print(f"正在抓取频道 {cid}...")
    chromedriver_autoinstaller.install()
    
    options = Options()
    options.add_argument('--headless')  # 无头模式
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # 代理配置（连接你的台湾 VPS）
    sw_options = {
        'proxy': {
            'http': 'http://127.0.0.1:7890',
            'https': 'http://127.0.0.1:7890',
        }
    }

    driver = None
    try:
        driver = webdriver.Chrome(options=options, seleniumwire_options=sw_options)
        driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
        
        # 模拟真人等待加载
        time.sleep(12)
        
        # 拦截所有网络请求
        for request in driver.requests:
            if 'master.m3u8' in request.url:
                match = re.search(r'playlist/([a-zA-Z0-9_-]+)/', request.url)
                if match:
                    aid = match.group(1)
                    print(f"🎯 成功拦截 {cid}: {aid}")
                    return aid
    except Exception as e:
        print(f"❌ {cid} 抓取异常: {e}")
    finally:
        if driver: driver.quit()
    return None

def main():
    channels = {
        'lhtv01': 'litv-longturn03',
        'lhtv03': 'litv-longturn02',
        'lhtv05': 'ofiii73',
        'lhtv06': 'ofiii74',
        'lhtv07': 'ofiii76',
    }
    
    workers_path = "workers.js"
    if not os.path.exists(workers_path): return
    with open(workers_path, "r", encoding="utf-8") as f: content = f.read()

    any_updated = False
    for cid, slug in channels.items():
        aid = get_asset_id(cid, slug)
        if aid:
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]+?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                any_updated = True
        time.sleep(2)

    if any_updated:
        with open(workers_path, "w", encoding="utf-8") as f: f.write(content)
        print("🚀 数据同步至 workers.js 完成")

if __name__ == "__main__":
    main()
